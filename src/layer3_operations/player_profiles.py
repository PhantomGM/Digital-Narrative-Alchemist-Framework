from typing import Dict, List, Optional, Sequence

from layer3_operations.safety_register import (
    LINE, SCENE, SafetyConstraint, SafetyRegister)


class PlayerProfileManager:
    """
    Acts as a registry for human players.

    Stores their playstyle preferences, character mappings, and specific safety
    boundaries (Lines & Veils) to be dynamically injected into the
    SafetyGovernor and into generation via ContextPackage.safety.

    Two ways in, deliberately:

    `register_player` takes a flat list of strings and is kept for callers that
    already use it. Everything it receives is treated as a LINE at SCENE scope,
    because that is the strictest reading available and guessing softer would
    be the wrong error to make.

    `register_profile` takes SafetyConstraints and is the real path. The flat
    list cannot represent a single distinction the Session 0 trial produced --
    Line versus Veil, a Line that is about on-screen death rather than the
    content existing, a Line that binds the setting rather than any scene --
    and a structure that cannot hold what players say will lose it.
    """

    def __init__(self):
        self._profiles: Dict[str, dict] = {}

    # ── Registration ────────────────────────────────────────

    def register_player(self, player_id: str, lines_and_veils: List[str] = None,
                        preferences: str = ""):
        """Legacy path: an undifferentiated list, read strictly as Lines."""
        if lines_and_veils is None:
            lines_and_veils = []
        constraints = [SafetyConstraint(text=t, kind=LINE, scope=SCENE,
                                        holders=(player_id,))
                       for t in lines_and_veils if str(t).strip()]
        self._profiles[player_id] = {
            "lines_and_veils": list(lines_and_veils),
            "constraints": constraints,
            "preferences": preferences,
        }
        print(f"[PlayerProfileManager] Registered '{player_id}' with "
              f"{len(constraints)} Lines & Veils.")

    def register_profile(self, player_id: str,
                         constraints: Sequence[SafetyConstraint] = (),
                         preferences: str = ""):
        """Structured path: constraints that know what kind of thing they are."""
        owned = [SafetyConstraint(text=c.text, kind=c.kind, scope=c.scope,
                                  note=c.note,
                                  holders=tuple(c.holders) or (player_id,))
                 for c in constraints]
        self._profiles[player_id] = {
            "lines_and_veils": [c.text for c in owned],
            "constraints": owned,
            "preferences": preferences,
        }
        n_lines = sum(1 for c in owned if c.kind == LINE)
        print(f"[PlayerProfileManager] Registered '{player_id}' with "
              f"{n_lines} Line(s) and {len(owned) - n_lines} Veil(s).")

    # ── Retrieval ───────────────────────────────────────────

    def get_player_profile(self, player_id: str) -> dict:
        return self._profiles.get(
            player_id, {"lines_and_veils": [], "constraints": [], "preferences": ""})

    def register(self, active_player_ids: Optional[Sequence[str]] = None
                 ) -> SafetyRegister:
        """
        The merged register for the given players, or the whole table.

        Merging keeps the stricter reading of any disagreement, so a boundary
        two players share can never come out weaker than either stated it.
        """
        ids = list(active_player_ids) if active_player_ids else list(self._profiles)
        merged = SafetyRegister()
        for pid in ids:
            for constraint in self.get_player_profile(pid).get("constraints", []):
                merged.add(constraint)
        return merged.merged()

    def safety_block(self, active_player_ids: Optional[Sequence[str]] = None) -> str:
        """The rendered block for ContextPackage.safety. Never names holders."""
        return self.register(active_player_ids).render()

    def aggregate_safety_boundaries(self, active_player_ids: List[str]) -> str:
        """
        The SafetyGovernor's view. Kept, but no longer flattening: the governor
        now receives Lines and Veils under separate headings, so it can tell
        "never" from "not on screen" -- which it previously could not.
        """
        block = self.safety_block(active_player_ids)
        if not block:
            return "No specific triggers listed. Maintain general PG-13 safety."
        return block
