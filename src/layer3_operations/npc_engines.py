"""
NPC behaviour and voice engines.

Design stubs: the interfaces are settled but the bodies are placeholders, so
determine_action() always waits and generate_dialogue() echoes the intention.
Nothing else in the tree implements these, so they are kept as the intended
shape of the feature rather than removed.

This module did not parse until now. Its docstrings were written with
backslash-escaped quote characters, which are only meaningful inside a string
and cannot open one. It has been broken since the initial commit, so there is
no intact version in history to restore.
"""


class NPCActorEngine:
    """Drives NPC behavior, goals, off-screen activity, and tactical/social choices based on phenotype."""

    def determine_action(self, npc_phenotype: dict, context: str) -> dict:
        return {"action": "wait", "reason": "No immediate threat"}


class NPCPersonaEngine:
    """Dictates how an NPC expresses themselves (voice, tone, deception, emotional posture)."""

    def generate_dialogue(self, npc_phenotype: dict, intention: str) -> str:
        return f"NPC says: I intend to {intention}"
