import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from layer2_narrative.event_ledger import EventLedger, StateEvent
from layer1_core.world_state import WorldStateKeeper

async def run_db_test():
    print("=== Testing Async DB Initialization ===")
    ledger = EventLedger(db_path="dna_ledger_test.db")
    await ledger.initialize_db()
    
    state_keeper = WorldStateKeeper(event_ledger=ledger)
    
    print("\n=== Testing Concurrent Writes ===")
    await asyncio.gather(
        state_keeper.update_reality("Test Cave", {"entities": ["Hero", "Slime"], "hazards": ["Pit"]}),
        state_keeper.update_reality("Global", {"weather": "Raining"}),
        state_keeper.ingest_history_data({"world_name": "Aethelgard", "timeline_year": 1200})
    )
    print("-> Concurrent Async Writes Successful")
    
    print("\n=== Testing Concurrent Reads ===")
    context, snapshot, ts = await asyncio.gather(
        state_keeper.get_context_window("Test Cave", n=5),
        ledger.snapshot(),
        ledger.get_last_timestamp()
    )
    
    print("-> Context Fetched:", context['current_state'])
    print("-> Snapshot Targets:", list(snapshot.keys()))
    print("-> Last Timestamp:", ts)
    
    print("\n[SUCCESS] All Async DB methods successfully passed!")

if __name__ == "__main__":
    asyncio.run(run_db_test())
