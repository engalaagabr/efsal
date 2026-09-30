"""Timer service for the break countdown."""

from typing import Callable, Optional

from gi.repository import GLib

from app.utils.constants import DEFAULT_BREAK_COUNTDOWN


class TimerService:
    """Simple countdown timer for break durations.

    Counts down from a configured duration and fires a callback
    when complete.
    """

    def __init__(self, duration: int = DEFAULT_BREAK_COUNTDOWN):
        self._duration = duration
        self._remaining = duration
        self._running = False
        self._source_id: int = 0

        # Callbacks
        self.on_tick: Optional[Callable[[int], None]] = None
        self.on_complete: Optional[Callable[[], None]] = None

    @property
    def remaining(self) -> int:
        """Remaining seconds."""
        return self._remaining

    @property
    def is_running(self) -> bool:
        """Whether the countdown is active."""
        return self._running

    def start(self, duration: Optional[int] = None):
        """Start or restart the countdown.

        Args:
            duration: Optional override for countdown duration in seconds.
        """
        self.stop()
        if duration is not None:
            self._duration = duration
        self._remaining = self._duration
        self._running = True
        self._source_id = GLib.timeout_add(1000, self._tick)

    def stop(self):
        """Stop the countdown."""
        self._running = False
        if self._source_id:
            GLib.source_remove(self._source_id)
            self._source_id = 0

    def _tick(self) -> bool:
        """Called every second during countdown."""
        if not self._running:
            return False

        self._remaining -= 1

        if self.on_tick:
            self.on_tick(self._remaining)

        if self._remaining <= 0:
            self._running = False
            if self.on_complete:
                self.on_complete()
            return False

        return True
