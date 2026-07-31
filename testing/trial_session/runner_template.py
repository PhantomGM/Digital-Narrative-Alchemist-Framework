import argparse
import asyncio
import json
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent
REPO_ROOT = BASE.parents[1]
SRC_ROOT = REPO_ROOT / "src"
LOGS = BASE / "output_logs"
LOGS.mkdir(exist_ok=True)

for path in (REPO_ROOT, SRC_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def load_json(name: str) -> Any:
    with open(BASE / name, "r", encoding="utf-8") as f:
        return json.load(f)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def classify_prompt(prompt: str) -> str:
    lower = prompt.lower()
    ooc_markers = ["out of character", "ooc", "out-of-character"]
    has_ooc = any(marker in lower for marker in ooc_markers)
    has_ic = any(
        token in lower
        for token in [
            " i ",
            "i ",
            "i'",
            "i_",
            "my ",
            "attack",
            "ask ",
            "go ",
            "sneak",
            "push open",
            "tell me",
        ]
    )
    if has_ooc and has_ic:
        return "Mixed"
    if has_ooc:
        return "OOC"
    return "IC"


def normalize_for_json(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {str(k): normalize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_for_json(v) for v in value]
    if isinstance(value, tuple):
        return [normalize_for_json(v) for v in value]
    return value


def build_world_snapshot(world_state: dict, player_state: dict) -> tuple[str, dict]:
    location_tag = world_state.get("campaign", {}).get("current_location", "Port Marrow")
    entities = [player_state.get("name", "Player")]
    entities.extend(npc.get("name", "Unknown NPC") for npc in world_state.get("known_npcs", []))
    hazards = []
    if world_state.get("campaign", {}).get("tone"):
        hazards.append(f"Tone: {world_state['campaign']['tone']}")

    reality = {
        "entities": entities,
        "hazards": hazards,
        "lighting": world_state.get("campaign", {}).get("current_time", "Unknown"),
        "threads": world_state.get("active_threads", []),
        "known_locations": [loc.get("name", "Unknown") for loc in world_state.get("known_locations", [])],
    }
    return location_tag, reality


async def build_director(world_state: dict, player_state: dict):
    from layer1_core.orchestrator import Orchestrator
    from layer1_core.world_state import WorldStateKeeper
    from layer2_narrative.event_ledger import EventLedger
    from layer2_narrative.narrative_weaver import NarrativeWeaver
    from layer3_operations.session_director import SessionDirector
    from layer4_rules.one_page_5e.arbiter import GameSystemArbiter as OnePage5eArbiter

    ledger_path = LOGS / "trial_ledger.db"
    event_ledger = EventLedger(db_path=str(ledger_path))
    state_keeper = WorldStateKeeper(event_ledger=event_ledger)

    location_tag, location_state = build_world_snapshot(world_state, player_state)
    state_keeper.state[location_tag] = location_state
    state_keeper.world_metadata.update(
        {
            "world_name": world_state.get("campaign", {}).get("title", "DNA Trial World"),
            "timeline_year": 1,
            "active_crises": world_state.get("active_threads", []),
            "significant_locations": [loc.get("name", "Unknown") for loc in world_state.get("known_locations", [])],
        }
    )

    orchestrator = Orchestrator()
    orchestrator.load_ruleset(OnePage5eArbiter())

    weaver = NarrativeWeaver()
    director = SessionDirector(orchestrator, weaver, state_keeper, registry=None)
    await director.state_keeper.event_ledger.initialize_db()

    player_id = player_state.get("name", "PC_01")
    goals = [player_state.get("current_goal", "Complete the current objective")]
    flaws = [player_state.get("class_style", "Unspecified style")]
    director.arc_tracker.register_pc(player_id, goals, flaws)
    director.profile_manager.register_player(
        player_id,
        lines_and_veils=[],
        preferences=player_state.get("class_style", ""),
    )
    return director, player_id, location_tag


def format_markdown_log(
    test: dict,
    response: str,
    notes: dict,
    location_tag: str,
    log_name: str,
    error: str | None = None,
) -> str:
    parts = [
        f"# {log_name}",
        "",
        f"## Test ID\n{test['id']}",
        "",
        f"## Category\n{test['category']}",
        "",
        f"## Prompt\n{test['prompt']}",
        "",
        "## Expectations",
    ]
    parts.extend(f"- {item}" for item in test.get("expectations", []))
    parts.extend(
        [
            "",
            f"## Trial Notes\n```json\n{json.dumps(normalize_for_json(notes), indent=2)}\n```",
            "",
            f"## Location Tag\n{location_tag}",
            "",
            "## Final Response",
            response,
            "",
            "## Quick Score",
            "- Routing: ",
            "- Consistency: ",
            "- In-Character Fidelity: ",
            "- Usability: ",
            "- Mechanical Restraint: ",
            "",
            "## Failure Notes",
            error or "[Fill this in after reviewing the output.]",
            "",
        ]
    )
    return "\n".join(parts)


async def run_test(test: dict, dry_run: bool = False) -> Path:
    world_state = load_json("sample_world_state.json")
    player_state = load_json("sample_player_state.json")
    location_tag, reality = build_world_snapshot(world_state, player_state)

    notes = {
        "intent_guess": classify_prompt(test["prompt"]),
        "world_facts": world_state.get("facts_that_must_not_change", []),
        "active_threads": world_state.get("active_threads", []),
        "player_goal": player_state.get("current_goal", ""),
        "location_state": reality,
        "dry_run": dry_run,
    }

    if dry_run:
        response = (
            "[DRY RUN] Replace this branch by calling the real pipeline. "
            "This mode exists so you can verify logging before spending API calls."
        )
        error = None
    else:
        response = ""
        error = None
        try:
            director, player_id, live_location_tag = await build_director(world_state, player_state)
            location_tag = live_location_tag
            response = await director.advance_scene(player_id, test["prompt"], location_tag)
        except Exception as exc:
            error = f"Pipeline execution failed: {exc}"
            response = "[PIPELINE ERROR] See failure notes below."

    timestamp = utc_stamp()
    log_name = f"{test['id']}_{timestamp}"
    out_path = LOGS / f"{log_name}.md"
    out_path.write_text(
        format_markdown_log(test, response, notes, location_tag, log_name, error=error),
        encoding="utf-8",
    )
    print(f"Wrote log: {out_path}")
    return out_path


async def run_many(selected_test_ids: list[str] | None = None, dry_run: bool = False) -> list[Path]:
    tests = load_json("test_prompts.json")
    selected = [t for t in tests if not selected_test_ids or t["id"] in selected_test_ids]
    if not selected:
        raise SystemExit("No matching test IDs found.")

    outputs = []
    for test in selected:
        outputs.append(await run_test(test, dry_run=dry_run))
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run trial-session prompts through the DNA pipeline.")
    parser.add_argument(
        "--test-id",
        action="append",
        dest="test_ids",
        help="Specific test ID to run. Repeat for multiple IDs. Defaults to all tests.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip live DNA calls and just exercise the logging pipeline.",
    )
    return parser.parse_args()


async def async_main() -> None:
    args = parse_args()
    outputs = await run_many(selected_test_ids=args.test_ids, dry_run=args.dry_run)
    print("Completed tests:")
    for path in outputs:
        print(f"- {path}")


if __name__ == "__main__":
    asyncio.run(async_main())
