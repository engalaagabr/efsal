"""Settings model with JSON persistence for Efsal."""

import json
import os
from pathlib import Path
from typing import Optional

from app.utils.constants import (
    CONFIG_DIR_NAME,
    CONFIG_FILE_NAME,
    DEFAULT_REMINDER_INTERVAL,
    DEFAULT_SNOOZE_DURATION,
)


class Settings:
    """Application settings with JSON file persistence.

    Uses XDG config directory (~/.config/efsal/settings.json).
    """

    def __init__(self):
        self._config_path = self._get_config_path()
        self._ensure_config_dir()

        # Defaults
        self.reminders_enabled: bool = True
        self.reminder_interval: int = DEFAULT_REMINDER_INTERVAL  # seconds
        self.snooze_duration: int = DEFAULT_SNOOZE_DURATION      # seconds
        self.autostart: bool = False
        self.pause_on_idle: bool = True
        self.reset_after_reminder: bool = True
        self.sound_enabled: bool = False
        self.show_popup: bool = True
        self.theme: str = "system"  # "system", "light", "dark"

        self.load()

    def _get_config_path(self) -> Path:
        """Get the XDG-compliant config file path."""
        config_home = os.environ.get(
            "XDG_CONFIG_HOME",
            os.path.expanduser("~/.config")
        )
        return Path(config_home) / CONFIG_DIR_NAME / CONFIG_FILE_NAME

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        """Load settings from disk. Uses defaults for missing keys."""
        if not self._config_path.exists():
            return

        try:
            with open(self._config_path, "r") as f:
                data = json.load(f)

            self.reminders_enabled = data.get("reminders_enabled", self.reminders_enabled)
            self.reminder_interval = data.get("reminder_interval", self.reminder_interval)
            self.snooze_duration = data.get("snooze_duration", self.snooze_duration)
            self.autostart = data.get("autostart", self.autostart)
            self.pause_on_idle = data.get("pause_on_idle", self.pause_on_idle)
            self.reset_after_reminder = data.get("reset_after_reminder", self.reset_after_reminder)
            self.sound_enabled = data.get("sound_enabled", self.sound_enabled)
            self.show_popup = data.get("show_popup", self.show_popup)
            self.theme = data.get("theme", self.theme)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not load settings: {e}")

    def save(self):
        """Persist current settings to disk."""
        data = {
            "reminders_enabled": self.reminders_enabled,
            "reminder_interval": self.reminder_interval,
            "snooze_duration": self.snooze_duration,
            "autostart": self.autostart,
            "pause_on_idle": self.pause_on_idle,
            "reset_after_reminder": self.reset_after_reminder,
            "sound_enabled": self.sound_enabled,
            "show_popup": self.show_popup,
            "theme": self.theme,
        }

        try:
            self._ensure_config_dir()
            with open(self._config_path, "w") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            print(f"Warning: Could not save settings: {e}")

    @property
    def reminder_interval_minutes(self) -> int:
        """Get reminder interval in minutes."""
        return self.reminder_interval // 60

    @reminder_interval_minutes.setter
    def reminder_interval_minutes(self, minutes: int):
        """Set reminder interval from minutes."""
        self.reminder_interval = minutes * 60

    @property
    def snooze_duration_minutes(self) -> int:
        """Get snooze duration in minutes."""
        return self.snooze_duration // 60

    @snooze_duration_minutes.setter
    def snooze_duration_minutes(self, minutes: int):
        """Set snooze duration from minutes."""
        self.snooze_duration = minutes * 60
