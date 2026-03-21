import os
import json
import sqlite3
import importlib

class GameSystemArbiter:
    def __init__(self, root_dir: str = None):
        if root_dir is None:
            self.root_dir = os.path.dirname(os.path.abspath(__file__))
        else:
            self.root_dir = root_dir
            
        with open(os.path.join(self.root_dir, "manifest.json"), "r", encoding="utf-8") as f:
            self.manifest = json.load(f)
            
        self._resolvers = {}
        
    def _get_resolver(self, module_key: str):
        """Lazy loads a resolver module based on manifest."""
        if module_key not in self._resolvers:
            module_path = self.manifest["resolver_modules"].get(module_key)
            if not module_path:
                raise ValueError(f"Resolver {module_key} not found in manifest.")
            
            # Using importlib to dynamically load the module
            try:
                mod = importlib.import_module(module_path)
                self._resolvers[module_key] = mod
            except ImportError as e:
                # If running directly from PF2EDNA, resolvers might not be a package in sys.path
                # We can fallback to loading via file path if needed, but import_module works if we're in the right directory.
                import sys
                if self.root_dir not in sys.path:
                    sys.path.insert(0, self.root_dir)
                mod = importlib.import_module(module_path)
                self._resolvers[module_key] = mod
                
        return self._resolvers[module_key]

    def resolve_action(self, action_type: str, context: dict) -> dict:
        """
        Routes the action to the appropriate executable tier resolver.
        Example action_type: 'attack_melee', 'save', 'skill_check'
        """
        if action_type in ["attack_melee", "attack_ranged"]:
            combat = self._get_resolver("combat")
            return combat.resolve_attack(
                attacker_mod=context.get("attack_mod", 0), 
                target_ac=context.get("target_ac", 10),
                attack_count=context.get("attack_count", 1),
                agile=context.get("agile", False)
            )
        elif action_type == "save":
            saves = self._get_resolver("saves")
            return saves.resolve_save(
                save_modifier=context.get("save_modifier", 0),
                dc=context.get("dc", 10),
                save_type=context.get("save_type", "reflex")
            )
        elif action_type == "skill_check":
            sc = self._get_resolver("skill_checks")
            return sc.resolve_check(
                skill_modifier=context.get("skill_modifier", 0),
                dc=context.get("dc", 10),
                skill_name=context.get("skill", "Acrobatics")
            )
        elif action_type == "damage":
            hp = self._get_resolver("hp")
            return hp.apply_damage(
                hp=context.get("hp", 10),
                amount=context.get("amount", 0),
                damage_type=context.get("damage_type", "slashing"),
                resistances=context.get("resistances", {}),
                weaknesses=context.get("weaknesses", {}),
                immunities=context.get("immunities", [])
            )
        else:
            raise NotImplementedError(f"Action '{action_type}' not currently mapped in Arbiter.")

    def query_data(self, dataset_name: str, query_params: dict) -> dict:
        """
        Queries tabular data (JSON or SQLite) specified in the manifest.
        Example dataset_name: 'conditions', 'spells'
        """
        file_rel_path = self.manifest["data_files"].get(dataset_name)
        if not file_rel_path:
            raise ValueError(f"Dataset '{dataset_name}' not found in manifest.")
            
        full_path = os.path.join(self.root_dir, file_rel_path)
        
        if full_path.endswith(".json"):
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Simple list iteration filter
            results = []
            for item in data:
                match = True
                for k, v in query_params.items():
                    # Case insensitive simple match for strings
                    if isinstance(item.get(k), str) and isinstance(v, str):
                        if v.lower() not in item.get(k, "").lower():
                            match = False
                            break
                    elif item.get(k) != v:
                        match = False
                        break
                if match:
                    results.append(item)
            return {"results": results}
            
        elif full_path.endswith(".db"):
            conn = sqlite3.connect(full_path)
            c = conn.cursor()
            
            # Very simple query builder
            conditions = []
            params = []
            for k, v in query_params.items():
                conditions.append(f"{k} = ?")
                params.append(v)
                
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            try:
                c.execute(f"SELECT * FROM {dataset_name}{where_clause}", tuple(params))
                # Get column names
                cols = [description[0] for description in c.description]
                rows = c.fetchall()
                results = [dict(zip(cols, row)) for row in rows]
            except sqlite3.OperationalError:
                # Table might not exist or schema mismatch
                results = []
            finally:
                conn.close()
                
            return {"results": results}
            
        else:
            raise ValueError(f"Unsupported data format for {full_path}")

    def get_knowledge(self, topic: str) -> str:
        """
        Returns raw markdown semantic knowledge for the given topic.
        """
        file_rel_path = self.manifest["knowledge_files"].get(topic)
        if not file_rel_path:
            raise ValueError(f"Knowledge topic '{topic}' not found in manifest.")
            
        full_path = os.path.join(self.root_dir, file_rel_path)
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

# --- SMOKE TEST ---
if __name__ == "__main__":
    a = GameSystemArbiter()
    print("Testing combat resolution...")
    res = a.resolve_action('attack_melee', {'attack_mod': 8, 'target_ac': 16, 'weapon': 'longsword', 'damage_dice': '1d8+4'})
    print(res)
    assert 'degree_of_success' in res
    
    print("Testing data query (skills)...")
    data_res = a.query_data('skills', {'name': 'Athletics'})
    print(data_res)
    assert len(data_res['results']) == 1
    
    print("Testing knowledge retrieval...")
    k = a.get_knowledge('roleplay')
    print(k[:50] + "...")
    assert len(k) > 10
    
    print("Arbiter MVC targets successfully validated!")
