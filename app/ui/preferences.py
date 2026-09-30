"""Preferences window using Libadwaita components."""

import os
from pathlib import Path

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from app.models.settings import Settings
from app.utils.constants import (
    APP_ID, AUTOSTART_DESKTOP_FILENAME,
    REMINDER_PRESETS, SNOOZE_PRESETS,
)


class PreferencesWindow(Adw.PreferencesWindow):
    """GNOME-native preferences window built with Libadwaita."""

    def __init__(self, application, settings: Settings):
        super().__init__(
            application=application,
            title="Preferences",
            default_width=600,
            default_height=700,
            modal=True,
            search_enabled=False,
        )
        self._settings = settings
        self._build_ui()
        self.connect("close-request", self._on_close)

    def _build_ui(self):
        """Build the preferences UI with Adw preference groups."""
        # --- Reminders Page ---
        reminders_page = Adw.PreferencesPage()
        reminders_page.set_title("Reminders")
        reminders_page.set_icon_name("alarm-symbolic")

        # Reminders group
        reminder_group = Adw.PreferencesGroup()
        reminder_group.set_title("Reminders")
        reminder_group.set_description(
            "Configure when and how you get reminded"
        )

        # Enable reminders toggle
        self._enable_row = Adw.SwitchRow()
        self._enable_row.set_title("Enable reminders")
        self._enable_row.set_subtitle(
            "Show a notification when it's time to take a break"
        )
        self._enable_row.set_active(self._settings.reminders_enabled)
        self._enable_row.connect("notify::active", self._on_enable_changed)
        reminder_group.add(self._enable_row)

        # Reminder interval
        self._interval_row = Adw.ActionRow()
        self._interval_row.set_title("Reminder interval")
        self._interval_row.set_subtitle("How often to remind you (minutes)")
        self._interval_spin = Gtk.SpinButton.new_with_range(1, 480, 1)
        self._interval_spin.set_valign(Gtk.Align.CENTER)
        self._interval_spin.set_value(self._settings.reminder_interval_minutes)
        self._interval_spin.connect("value-changed", self._on_interval_changed)
        self._interval_row.add_suffix(self._interval_spin)
        reminder_group.add(self._interval_row)

        # Snooze duration
        self._snooze_row = Adw.ActionRow()
        self._snooze_row.set_title("Snooze duration")
        self._snooze_row.set_subtitle("How long to wait when you snooze (minutes)")
        self._snooze_spin = Gtk.SpinButton.new_with_range(1, 60, 1)
        self._snooze_spin.set_valign(Gtk.Align.CENTER)
        self._snooze_spin.set_value(self._settings.snooze_duration_minutes)
        self._snooze_spin.connect("value-changed", self._on_snooze_changed)
        self._snooze_row.add_suffix(self._snooze_spin)
        reminder_group.add(self._snooze_row)

        reminders_page.add(reminder_group)

        # Notification group
        notif_group = Adw.PreferencesGroup()
        notif_group.set_title("Notifications")

        self._popup_row = Adw.SwitchRow()
        self._popup_row.set_title("Show popup window")
        self._popup_row.set_subtitle(
            "Display a popup in addition to the notification"
        )
        self._popup_row.set_active(self._settings.show_popup)
        self._popup_row.connect("notify::active", self._on_popup_changed)
        notif_group.add(self._popup_row)

        self._sound_row = Adw.SwitchRow()
        self._sound_row.set_title("Enable sound")
        self._sound_row.set_subtitle(
            "Play a gentle sound with the reminder"
        )
        self._sound_row.set_active(self._settings.sound_enabled)
        self._sound_row.connect("notify::active", self._on_sound_changed)
        notif_group.add(self._sound_row)

        reminders_page.add(notif_group)
        self.add(reminders_page)

        # --- Behavior Page ---
        behavior_page = Adw.PreferencesPage()
        behavior_page.set_title("Behavior")
        behavior_page.set_icon_name("preferences-system-symbolic")

        behavior_group = Adw.PreferencesGroup()
        behavior_group.set_title("Tracking")

        self._idle_row = Adw.SwitchRow()
        self._idle_row.set_title("Pause when idle")
        self._idle_row.set_subtitle(
            "Stop counting active time when you're away"
        )
        self._idle_row.set_active(self._settings.pause_on_idle)
        self._idle_row.connect("notify::active", self._on_idle_changed)
        behavior_group.add(self._idle_row)

        self._reset_row = Adw.SwitchRow()
        self._reset_row.set_title("Reset after reminder")
        self._reset_row.set_subtitle(
            "Reset the timer when you acknowledge a break"
        )
        self._reset_row.set_active(self._settings.reset_after_reminder)
        self._reset_row.connect("notify::active", self._on_reset_changed)
        behavior_group.add(self._reset_row)

        behavior_page.add(behavior_group)

        # Startup group
        startup_group = Adw.PreferencesGroup()
        startup_group.set_title("Startup")

        self._autostart_row = Adw.SwitchRow()
        self._autostart_row.set_title("Start at login")
        self._autostart_row.set_subtitle(
            "Automatically start when you log into GNOME"
        )
        self._autostart_row.set_active(self._settings.autostart)
        self._autostart_row.connect(
            "notify::active", self._on_autostart_changed
        )
        startup_group.add(self._autostart_row)

        behavior_page.add(startup_group)

        # Appearance group
        appearance_group = Adw.PreferencesGroup()
        appearance_group.set_title("Appearance")

        self._theme_row = Adw.ComboRow()
        self._theme_row.set_title("Theme")
        theme_model = Gtk.StringList()
        themes = ["Follow system", "Light", "Dark"]
        theme_keys = ["system", "light", "dark"]
        theme_idx = 0
        for i, name in enumerate(themes):
            theme_model.append(name)
            if theme_keys[i] == self._settings.theme:
                theme_idx = i
        self._theme_row.set_model(theme_model)
        self._theme_row.set_selected(theme_idx)
        self._theme_row.connect("notify::selected", self._on_theme_changed)
        appearance_group.add(self._theme_row)

        behavior_page.add(appearance_group)
        self.add(behavior_page)

    # --- Setting change handlers ---

    def _on_enable_changed(self, row, _pspec):
        self._settings.reminders_enabled = row.get_active()
        self._settings.save()

    def _on_interval_changed(self, spinbutton):
        self._settings.reminder_interval_minutes = int(spinbutton.get_value())
        self._settings.save()

    def _on_snooze_changed(self, spinbutton):
        self._settings.snooze_duration_minutes = int(spinbutton.get_value())
        self._settings.save()

    def _on_popup_changed(self, row, _pspec):
        self._settings.show_popup = row.get_active()
        self._settings.save()

    def _on_sound_changed(self, row, _pspec):
        self._settings.sound_enabled = row.get_active()
        self._settings.save()

    def _on_idle_changed(self, row, _pspec):
        self._settings.pause_on_idle = row.get_active()
        self._settings.save()

    def _on_reset_changed(self, row, _pspec):
        self._settings.reset_after_reminder = row.get_active()
        self._settings.save()

    def _on_autostart_changed(self, row, _pspec):
        self._settings.autostart = row.get_active()
        self._settings.save()
        self._update_autostart_file(row.get_active())

    def _on_theme_changed(self, row, _pspec):
        theme_keys = ["system", "light", "dark"]
        idx = row.get_selected()
        if 0 <= idx < len(theme_keys):
            self._settings.theme = theme_keys[idx]
            self._settings.save()
            self._apply_theme(theme_keys[idx])

    def _apply_theme(self, theme: str):
        """Apply the selected color scheme."""
        style_manager = Adw.StyleManager.get_default()
        schemes = {
            "system": Adw.ColorScheme.DEFAULT,
            "light": Adw.ColorScheme.FORCE_LIGHT,
            "dark": Adw.ColorScheme.FORCE_DARK,
        }
        style_manager.set_color_scheme(
            schemes.get(theme, Adw.ColorScheme.DEFAULT)
        )

    def _update_autostart_file(self, enable: bool):
        """Create or remove the XDG autostart .desktop file."""
        autostart_dir = Path(os.environ.get(
            "XDG_CONFIG_HOME",
            os.path.expanduser("~/.config")
        )) / "autostart"
        autostart_file = autostart_dir / AUTOSTART_DESKTOP_FILENAME

        if enable:
            autostart_dir.mkdir(parents=True, exist_ok=True)
            # Find the project directory
            project_dir = Path(__file__).resolve().parent.parent.parent
            desktop_content = f"""[Desktop Entry]
Type=Application
Name=Efsal
Comment=Wellness reminder to move, stretch, and hydrate
Exec=python3 -m app
Path={project_dir}
Icon=io.github.efsal
Terminal=false
Categories=Utility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""
            try:
                autostart_file.write_text(desktop_content)
            except OSError as e:
                print(f"Warning: Could not create autostart file: {e}")
        else:
            try:
                if autostart_file.exists():
                    autostart_file.unlink()
            except OSError as e:
                print(f"Warning: Could not remove autostart file: {e}")

    def _on_close(self, window):
        """Save settings when preferences window closes."""
        self._settings.save()
        return False
