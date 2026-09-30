"""Tests for ActivityTracker state machine logic."""

import time
import unittest
from unittest.mock import MagicMock, PropertyMock

from app.services.activity_tracker import ActivityTracker, TrackerState
from app.models.settings import Settings
from app.services.idle_detector import IdleDetector


class MockIdleDetector:
    """A mock idle detector for testing."""

    def __init__(self):
        self._idle = False
        self._available = True

    def is_idle(self):
        return self._idle

    def is_active(self):
        return not self._idle

    @property
    def available(self):
        return self._available

    def set_idle(self, idle: bool):
        self._idle = idle


class TestActivityTracker(unittest.TestCase):
    """Tests for ActivityTracker state transitions."""

    def setUp(self):
        # Create settings with defaults (in-memory, no file I/O)
        self.settings = MagicMock(spec=Settings)
        self.settings.reminder_interval = 2700  # 45 minutes
        self.settings.snooze_duration = 300  # 5 minutes
        self.settings.reminders_enabled = True
        self.settings.pause_on_idle = True
        self.settings.reset_after_reminder = True

        self.idle_detector = MockIdleDetector()
        self.tracker = ActivityTracker(self.settings, self.idle_detector)

    def test_initial_state(self):
        self.assertEqual(self.tracker.state, TrackerState.TRACKING)
        self.assertEqual(self.tracker.accumulated_seconds, 0)
        self.assertEqual(self.tracker.seconds_remaining, 2700)

    def test_pause_resume(self):
        self.tracker.pause()
        self.assertEqual(self.tracker.state, TrackerState.PAUSED)

        self.tracker.resume()
        self.assertEqual(self.tracker.state, TrackerState.TRACKING)

    def test_pause_from_idle(self):
        """Can pause while idle."""
        self.tracker._state = TrackerState.IDLE
        self.tracker.pause()
        self.assertEqual(self.tracker.state, TrackerState.PAUSED)

    def test_reset(self):
        self.tracker._accumulated_seconds = 1500
        self.tracker.reset()
        self.assertEqual(self.tracker.accumulated_seconds, 0)
        self.assertEqual(self.tracker.state, TrackerState.TRACKING)

    def test_reset_while_paused_stays_paused(self):
        self.tracker.pause()
        self.tracker._accumulated_seconds = 500
        self.tracker.reset()
        self.assertEqual(self.tracker.accumulated_seconds, 0)
        self.assertEqual(self.tracker.state, TrackerState.PAUSED)

    def test_snooze(self):
        self.tracker.snooze()
        self.assertEqual(self.tracker.state, TrackerState.SNOOZED)

    def test_progress(self):
        self.tracker._accumulated_seconds = 1350  # Half of 2700
        self.assertAlmostEqual(self.tracker.progress, 0.5, places=2)

    def test_progress_full(self):
        self.tracker._accumulated_seconds = 2700
        self.assertAlmostEqual(self.tracker.progress, 1.0, places=2)

    def test_progress_over(self):
        self.tracker._accumulated_seconds = 3000
        self.assertAlmostEqual(self.tracker.progress, 1.0, places=2)

    def test_seconds_remaining(self):
        self.tracker._accumulated_seconds = 2000
        self.assertEqual(self.tracker.seconds_remaining, 700)

    def test_seconds_remaining_zero_floor(self):
        self.tracker._accumulated_seconds = 3000
        self.assertEqual(self.tracker.seconds_remaining, 0)

    def test_force_reminder(self):
        callback = MagicMock()
        self.tracker.on_threshold_reached = callback
        self.tracker.force_reminder()
        callback.assert_called_once()

    def test_start_break(self):
        self.tracker.start_break()
        self.assertEqual(self.tracker.state, TrackerState.BREAK)

    def test_end_break(self):
        self.tracker.start_break()
        self.tracker.end_break()
        self.assertEqual(self.tracker.accumulated_seconds, 0)
        self.assertEqual(self.tracker.state, TrackerState.TRACKING)

    def test_threshold_callback(self):
        """Threshold callback fires when accumulated >= interval."""
        callback = MagicMock()
        self.tracker.on_threshold_reached = callback
        self.tracker._accumulated_seconds = 2700
        self.tracker._check_threshold()
        callback.assert_called_once()

    def test_threshold_not_fired_when_disabled(self):
        """No callback if reminders are disabled."""
        callback = MagicMock()
        self.tracker.on_threshold_reached = callback
        self.settings.reminders_enabled = False
        self.tracker._accumulated_seconds = 2700
        self.tracker._check_threshold()
        callback.assert_not_called()

    def test_state_change_callback(self):
        callback = MagicMock()
        self.tracker.on_state_changed = callback
        self.tracker.pause()
        callback.assert_called_with(TrackerState.PAUSED)


if __name__ == "__main__":
    unittest.main()
