"""Tests for Settings model."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from app.models.settings import Settings
from app.utils.constants import DEFAULT_REMINDER_INTERVAL, DEFAULT_SNOOZE_DURATION


class TestSettings(unittest.TestCase):
    """Tests for Settings persistence and defaults."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._config_env = {"XDG_CONFIG_HOME": self._tmpdir}

    def _make_settings(self):
        with patch.dict(os.environ, self._config_env):
            return Settings()

    def test_defaults(self):
        s = self._make_settings()
        self.assertTrue(s.reminders_enabled)
        self.assertEqual(s.reminder_interval, DEFAULT_REMINDER_INTERVAL)
        self.assertEqual(s.snooze_duration, DEFAULT_SNOOZE_DURATION)
        self.assertFalse(s.autostart)
        self.assertTrue(s.pause_on_idle)
        self.assertEqual(s.theme, "system")

    def test_save_and_load(self):
        s = self._make_settings()
        s.reminders_enabled = False
        s.reminder_interval_minutes = 30
        s.theme = "dark"
        s.save()

        s2 = self._make_settings()
        self.assertFalse(s2.reminders_enabled)
        self.assertEqual(s2.reminder_interval, 30 * 60)
        self.assertEqual(s2.theme, "dark")

    def test_interval_minutes_property(self):
        s = self._make_settings()
        s.reminder_interval_minutes = 60
        self.assertEqual(s.reminder_interval, 3600)
        self.assertEqual(s.reminder_interval_minutes, 60)

    def test_snooze_minutes_property(self):
        s = self._make_settings()
        s.snooze_duration_minutes = 10
        self.assertEqual(s.snooze_duration, 600)
        self.assertEqual(s.snooze_duration_minutes, 10)

    def test_corrupted_config(self):
        """Settings should handle corrupted config gracefully."""
        with patch.dict(os.environ, self._config_env):
            config_dir = os.path.join(self._tmpdir, "efsal")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "settings.json")
            with open(config_file, "w") as f:
                f.write("not valid json{{{")

            s = Settings()
            # Should fall back to defaults
            self.assertTrue(s.reminders_enabled)
            self.assertEqual(s.reminder_interval, DEFAULT_REMINDER_INTERVAL)


if __name__ == "__main__":
    unittest.main()
