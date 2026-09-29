"""
Module   : ABDM Sync Worker
Owner    : Integration Engineer
Purpose  : Async retry worker for failed FHIR/ABDM pushes.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from backend.config import settings
from backend.services.fhir_service import push_to_abdm


@dataclass
class RetryJob:
    bundle: dict[str, Any]
    patient_id: str
    attempt: int = 0
    max_attempts: int = 5
    created_at: float = field(default_factory=time.time)
    last_error: str | None = None


class ABDMSyncWorker:
    """Background worker that retries failed ABDM pushes with exponential backoff."""

    def __init__(self):
        self._queue: asyncio.Queue[RetryJob] = asyncio.Queue()
        self._dead_letter: list[RetryJob] = []
        self._running = False
        self._base_delay = 5.0  # seconds
        self._max_delay = 300.0  # 5 minutes

    async def run(self, shutdown_event: asyncio.Event) -> None:
        """Main worker loop."""
        self._running = True
        print("[abdm_worker] Started")

        while not shutdown_event.is_set():
            try:
                # Wait for a job with timeout to check shutdown
                try:
                    job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except TimeoutError:
                    continue

                await self._process_job(job)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                print(f"[abdm_worker] Error: {exc}")
                await asyncio.sleep(5)

        self._running = False
        print(f"[abdm_worker] Stopped. Dead letter queue: {len(self._dead_letter)} jobs")

    async def _process_job(self, job: RetryJob) -> None:
        """Process a single retry job."""
        delay = min(self._base_delay * (2 ** job.attempt), self._max_delay)

        if job.attempt > 0:
            print(f"[abdm_worker] Retrying job for patient {job.patient_id} (attempt {job.attempt + 1}) after {delay}s")
            await asyncio.sleep(delay)

        result = push_to_abdm(
            bundle=job.bundle,
            client_id=settings.abdm_client_id,
            client_secret=settings.abdm_client_secret,
            base_url=settings.abdm_base_url,
        )

        if result.success:
            print(f"[abdm_worker] Push succeeded for patient {job.patient_id}")
            # In production: update audit log, notify patient, etc.
        else:
            job.attempt += 1
            job.last_error = result.message
            if job.attempt >= job.max_attempts:
                print(f"[abdm_worker] Job for patient {job.patient_id} exceeded max attempts, moving to dead letter")
                self._dead_letter.append(job)
            else:
                # Re-queue for retry
                await self._queue.put(job)

    def enqueue_push(self, bundle: dict[str, Any], patient_id: str) -> None:
        """Enqueue a FHIR bundle for pushing to ABDM."""
        job = RetryJob(bundle=bundle, patient_id=patient_id)
        self._queue.put_nowait(job)

    def get_dead_letter(self) -> list[dict[str, Any]]:
        """Get dead letter jobs for inspection."""
        return [
            {
                "patient_id": job.patient_id,
                "attempts": job.attempt,
                "last_error": job.last_error,
                "created_at": job.created_at,
            }
            for job in self._dead_letter
        ]
