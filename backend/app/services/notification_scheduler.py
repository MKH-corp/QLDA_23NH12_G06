import asyncio
import logging
from contextlib import suppress

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.notification_engine import NotificationEngine

logger = logging.getLogger(__name__)


class NotificationScheduler:
    def __init__(self, interval_seconds: int | None = None) -> None:
        self.interval_seconds = interval_seconds or settings.notification_scheduler_interval_seconds
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    def start(self) -> None:
        if not settings.notification_scheduler_enabled or self._task is not None:
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run(), name="notification-scheduler")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop_event.set()
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            self.run_once()
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval_seconds)
            except TimeoutError:
                continue

    @staticmethod
    def run_once() -> None:
        db = SessionLocal()
        try:
            NotificationEngine(db).check_all()
        except Exception:
            db.rollback()
            logger.exception("Notification scheduler run failed")
        finally:
            db.close()
