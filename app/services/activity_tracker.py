"""Activity tracker service — the core state machine for Efsal.

Tracks accumulated active time, handles idle transitions,
and fires callbacks when the reminder threshold is reached.
"""

import time
from enum import Enum, auto
from typing import Callable, Optional

from gi.repository import GLib

from app.services.idle_detector import IdleDetector
from app.models.settings import Settings
from app.utils.constants import IDLE_POLL_INTERVAL, UI_UPDATE_INTERVAL


class TrackerState(Enum):
    """Possible states for the activity tracker."""
    TRACKING = auto()   # Actively counting time
    IDLE = auto()       # User is idle, accumulation paused
    PAUSED = auto()     # User manually paused tracking
    BREAK = auto()      # Currently in a break
    SNOOZED = auto()    # Reminder was snoozed


class ActivityTracker:
    """Tracks accumulated active computer usage time.

    This is the core brain of the application. It:
    - Polls idle state periodically
    - Accumulates active seconds
    - Fires on_threshold_reached when the reminder interval is hit
    - Supports pause/resume, snooze, and reset
    """

    def __init__(self, settings: Settings, idle_detector: IdleDetector):
        self._settings = settings
        self._idle_detector = idle_detector

        # Core state
        self._state = TrackerState.TRACKING
        self._accumulated_seconds: int = 0
        self._last_tick_time: float = time.monotonic()
        self._snoozed_until: Optional[float] = None

        # GLib source IDs for cleanup
        self._idle_poll_source: int = 0
        self._ui_update_source: int = 0

        # Callbacks
        self.on_state_changed: Optional[Callable[[TrackerState], None]] = None
        self.on_time_updated: Optional[Callable[[int, int], None]] = None
        self.on_threshold_reached: Optional[Callable[[], None]] = None

    @property
    def state(self) -> TrackerState:
        """Current tracker state."""
        return self._state

    @property
    def accumulated_seconds(self) -> int:
        """Total accumulated active seconds in this session."""
        return self._accumulated_seconds

    @property
    def seconds_remaining(self) -> int:
        """Seconds remaining until next reminder."""
        remaining = self._settings.reminder_interval - self._accumulated_seconds
        return max(0, remaining)

    @property
    def progress(self) -> float:
        """Progress toward next reminder (0.0 to 1.0)."""
        if self._settings.reminder_interval <= 0:
            return 0.0
        return min(1.0, self._accumulated_seconds / self._settings.reminder_interval)

    @property
    def is_tracking(self) -> bool:
        """Whether the tracker is actively accumulating time."""
        return self._state == TrackerState.TRACKING

    def start(self):
        """Start the tracking loop."""
        self._last_tick_time = time.monotonic()
        self._state = TrackerState.TRACKING
        self._start_polling()
        self._notify_state_changed()

    def stop(self):
        """Stop all polling."""
        self._stop_polling()

    def pause(self):
        """Manually pause tracking."""
        if self._state in (TrackerState.TRACKING, TrackerState.IDLE):
            self._state = TrackerState.PAUSED
            self._notify_state_changed()

    def resume(self):
        """Resume tracking after manual pause."""
        if self._state == TrackerState.PAUSED:
            self._last_tick_time = time.monotonic()
            self._state = TrackerState.TRACKING
            self._notify_state_changed()

    def reset(self):
        """Reset accumulated time to zero."""
        self._accumulated_seconds = 0
        self._snoozed_until = None
        if self._state != TrackerState.PAUSED:
            self._state = TrackerState.TRACKING
            self._last_tick_time = time.monotonic()
        self._notify_state_changed()
        self._notify_time_updated()

    def snooze(self):
        """Snooze the reminder for the configured duration."""
        self._snoozed_until = time.monotonic() + self._settings.snooze_duration
        self._state = TrackerState.SNOOZED
        self._last_tick_time = time.monotonic()
        self._notify_state_changed()

    def start_break(self):
        """Enter break mode."""
        self._state = TrackerState.BREAK
        self._notify_state_changed()

    def end_break(self):
        """End break and reset timer."""
        self.reset()

    def force_reminder(self):
        """Force-trigger the reminder callback (for 'Take a break now')."""
        if self.on_threshold_reached:
            self.on_threshold_reached()

    def _start_polling(self):
        """Start the GLib periodic timers."""
        self._stop_polling()
        self._idle_poll_source = GLib.timeout_add(
            IDLE_POLL_INTERVAL, self._on_idle_poll
        )
        self._ui_update_source = GLib.timeout_add(
            UI_UPDATE_INTERVAL, self._on_ui_tick
        )

    def _stop_polling(self):
        """Remove GLib timer sources."""
        if self._idle_poll_source:
            GLib.source_remove(self._idle_poll_source)
            self._idle_poll_source = 0
        if self._ui_update_source:
            GLib.source_remove(self._ui_update_source)
            self._ui_update_source = 0

    def _on_idle_poll(self) -> bool:
        """Periodic check for idle/active transitions.

        Returns True to keep the timer running.
        """
        if self._state == TrackerState.PAUSED:
            return True

        if self._state == TrackerState.BREAK:
            return True

        now = time.monotonic()
        is_idle = (
            self._settings.pause_on_idle
            and self._idle_detector.is_idle()
        )

        if self._state == TrackerState.SNOOZED:
            # Check if snooze has expired
            if self._snoozed_until and now >= self._snoozed_until:
                self._snoozed_until = None
                self._state = TrackerState.TRACKING
                self._last_tick_time = now
                self._notify_state_changed()
                # Check if we should trigger immediately
                self._check_threshold()
            return True

        if is_idle:
            if self._state == TrackerState.TRACKING:
                self._state = TrackerState.IDLE
                self._notify_state_changed()
        else:
            if self._state == TrackerState.IDLE:
                self._state = TrackerState.TRACKING
                self._last_tick_time = now
                self._notify_state_changed()

        return True

    def _on_ui_tick(self) -> bool:
        """Called every second to accumulate time and update the UI.

        Returns True to keep the timer running.
        """
        if self._state == TrackerState.TRACKING:
            now = time.monotonic()
            elapsed = now - self._last_tick_time
            self._last_tick_time = now

            # Clamp elapsed to prevent jumps after suspend
            # If more than 10 seconds passed, cap at 1 second
            if elapsed > 10:
                elapsed = 0  # Likely suspend/resume, don't count

            self._accumulated_seconds += int(elapsed)
            self._notify_time_updated()
            self._check_threshold()

        elif self._state == TrackerState.SNOOZED:
            # Still accumulate during snooze
            now = time.monotonic()
            elapsed = now - self._last_tick_time
            self._last_tick_time = now
            if elapsed > 10:
                elapsed = 0
            self._accumulated_seconds += int(elapsed)
            self._notify_time_updated()

        elif self._state in (TrackerState.IDLE, TrackerState.PAUSED):
            # Reset tick time so we don't get a jump when resuming
            self._last_tick_time = time.monotonic()

        return True

    def _check_threshold(self):
        """Check if accumulated time has reached the reminder threshold."""
        if not self._settings.reminders_enabled:
            return

        if self._accumulated_seconds >= self._settings.reminder_interval:
            self.start_break()
            if self.on_threshold_reached:
                self.on_threshold_reached()

    def _notify_state_changed(self):
        """Notify listeners of state change."""
        if self.on_state_changed:
            self.on_state_changed(self._state)

    def _notify_time_updated(self):
        """Notify listeners of time update."""
        if self.on_time_updated:
            self.on_time_updated(
                self._accumulated_seconds,
                self.seconds_remaining
            )
