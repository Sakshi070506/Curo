"""
Module   : Worker Runner
Owner    : Backend Lead
Purpose  : Starts background workers (triage alerts, ABDM sync) locally.
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.workers.abdm_sync_worker import ABDMSyncWorker
from backend.workers.triage_alert_worker import TriageAlertWorker


async def main():
    print("[run_workers] Starting background workers...")

    triage_worker = TriageAlertWorker()
    abdm_worker = ABDMSyncWorker()

    # Handle shutdown signals
    shutdown_event = asyncio.Event()

    def signal_handler(signum, frame):
        print(f"[run_workers] Received signal {signum}, shutting down...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start workers
    triage_task = asyncio.create_task(triage_worker.run(shutdown_event))
    abdm_task = asyncio.create_task(abdm_worker.run(shutdown_event))

    try:
        await shutdown_event.wait()
    finally:
        print("[run_workers] Stopping workers...")
        triage_task.cancel()
        abdm_task.cancel()
        await asyncio.gather(triage_task, abdm_task, return_exceptions=True)
        print("[run_workers] Workers stopped.")


if __name__ == "__main__":
    asyncio.run(main())
