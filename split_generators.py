import ast
import os

source_file = r'C:\Users\nickd\Desktop\Vaults\DNA Notes\Master_Generator_Knowledge.py'
output_dir = r'C:\Users\nickd\Desktop\OC2\src\agents\layer2_dna\generators'
os.makedirs(output_dir, exist_ok=True)

with open(source_file, 'r', encoding='utf-8') as f:
    source_code = f.read()

tree = ast.parse(source_code)
lines = source_code.splitlines()

# Map function/class names to file names
name_map = {
    'generate_npc_dna': 'npc.py',
    'generate_faction_dna': 'faction.py',
    'generate_quest_dna': 'quest.py',
    'generate_item_dna': 'item.py',
    'generate_location_dna': 'location.py',
    'generate_travel_dna': 'travel.py',
    'generate_region_dna': 'region.py',
    'generate_realm_dna': 'realm.py',
    'generate_agency_dna': 'agency.py',
    'generate_trap_dna': 'trap.py',
    'generate_world_wonder_dna': 'wonder.py',
    'generate_establishment_dna': 'establishment.py',
    'generate_regional_poi_dna': 'regional_poi.py',
    'WorldDNAGenerator': 'world.py'
}

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        if node.name in name_map:
            file_name = name_map[node.name]
            file_content = "import random\n\n"
            
            start = node.lineno - 1
            if len(node.decorator_list) > 0:
                start = node.decorator_list[0].lineno - 1
            end = node.end_lineno
            body_code = "\n".join(lines[start:end])
            
            file_content += body_code + "\n"
            
            out_path = os.path.join(output_dir, file_name)
            with open(out_path, 'w', encoding='utf-8') as out_f:
                out_f.write(file_content)
                
            print(f"Created {file_name}")

init_content = ""
for func_name, file_name in name_map.items():
    mod_name = file_name.replace('.py', '')
    init_content += f"from .{mod_name} import {func_name}\n"

with open(os.path.join(output_dir, '__init__.py'), 'w', encoding='utf-8') as init_f:
    init_f.write(init_content)
print("Created __init__.py")
