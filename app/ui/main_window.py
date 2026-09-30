"""Main window for Efsal — the primary tracking interface."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, Pango

from app.services.activity_tracker import ActivityTracker, TrackerState
from app.utils.time_utils import format_duration, format_minutes_remaining


class MainWindow(Adw.ApplicationWindow):
    """Primary application window showing the active timer and status."""

    def __init__(self, application, tracker: ActivityTracker):
        super().__init__(
            application=application,
            title="Efsal",
            default_width=400,
            default_height=520,
            resizable=True,
        )
        self.set_hide_on_close(True)
        self._tracker = tracker
        self._app = application

        self._build_ui()
        self._connect_tracker()
        self._update_display(0, self._tracker.seconds_remaining)
        self._update_state_display(self._tracker.state)

    def _build_ui(self):
        """Construct the full window UI."""
        # Header bar
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(True)
        header.set_show_start_title_buttons(True)

        # Menu button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_tooltip_text("Menu")
        menu_button.set_menu_model(self._create_menu())
        header.pack_end(menu_button)

        # Main content
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.append(header)

        # Scrolled content area
        content = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=24,
            margin_start=24,
            margin_end=24,
            margin_top=32,
            margin_bottom=24,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
            vexpand=True,
        )

        # --- Timer Card ---
        timer_card = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
            halign=Gtk.Align.CENTER,
        )
        timer_card.add_css_class("timer-card")
        timer_card.set_margin_start(8)
        timer_card.set_margin_end(8)
        timer_card.set_margin_top(16)
        timer_card.set_margin_bottom(16)

        # Active time label
        active_label = Gtk.Label(label="Active time")
        active_label.add_css_class("caption")
        active_label.add_css_class("dim-label")
        active_label.set_margin_top(20)
        timer_card.append(active_label)

        # Big timer display
        self._timer_label = Gtk.Label(label="00:00")
        self._timer_label.add_css_class("timer-display")
        self._timer_label.set_halign(Gtk.Align.CENTER)
        timer_card.append(self._timer_label)

        # Remaining time label
        self._remaining_label = Gtk.Label(label="45 minutes until your next break")
        self._remaining_label.add_css_class("body")
        self._remaining_label.add_css_class("dim-label")
        self._remaining_label.set_wrap(True)
        self._remaining_label.set_justify(Gtk.Justification.CENTER)
        self._remaining_label.set_margin_bottom(8)
        timer_card.append(self._remaining_label)

        # Progress bar
        self._progress_bar = Gtk.ProgressBar()
        self._progress_bar.set_fraction(0.0)
        self._progress_bar.set_margin_start(20)
        self._progress_bar.set_margin_end(20)
        self._progress_bar.set_margin_bottom(20)
        timer_card.append(self._progress_bar)

        content.append(timer_card)

        # --- Status indicator ---
        status_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8,
            halign=Gtk.Align.CENTER,
        )

        self._status_dot = Gtk.Label(label="●")
        self._status_dot.add_css_class("status-dot-active")
        status_box.append(self._status_dot)

        self._status_label = Gtk.Label(label="Tracking")
        self._status_label.add_css_class("caption")
        status_box.append(self._status_label)

        content.append(status_box)

        # --- Action buttons ---
        button_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            halign=Gtk.Align.CENTER,
            margin_top=8,
        )

        # Pause/Resume button
        self._pause_button = Gtk.Button(label="Pause tracking")
        self._pause_button.add_css_class("pill")
        self._pause_button.set_size_request(200, -1)
        self._pause_button.connect("clicked", self._on_pause_clicked)
        button_box.append(self._pause_button)

        # Take a break button
        break_button = Gtk.Button(label="Take a break")
        break_button.add_css_class("pill")
        break_button.add_css_class("suggested-action")
        break_button.set_size_request(200, -1)
        break_button.connect("clicked", self._on_break_clicked)
        button_box.append(break_button)

        content.append(button_box)

        # Clamp for responsive sizing
        clamp = Adw.Clamp()
        clamp.set_maximum_size(500)
        clamp.set_child(content)
        clamp.set_vexpand(True)

        main_box.append(clamp)
        self.set_content(main_box)

    def _create_menu(self) -> Gio.Menu:
        """Create the hamburger menu model."""
        from gi.repository import Gio

        menu = Gio.Menu()
        menu.append("Preferences", "app.preferences")
        menu.append("Reset Timer", "app.reset-timer")
        menu.append("About Efsal", "app.about")
        menu.append("Quit", "app.quit")
        return menu

    def _connect_tracker(self):
        """Subscribe to tracker state changes."""
        self._tracker.on_time_updated = self._on_time_updated
        self._tracker.on_state_changed = self._on_state_changed

    def _on_time_updated(self, accumulated: int, remaining: int):
        """Called by tracker when time updates."""
        GLib.idle_add(self._update_display, accumulated, remaining)

    def _on_state_changed(self, state: TrackerState):
        """Called by tracker when state changes."""
        GLib.idle_add(self._update_state_display, state)

    def _update_display(self, accumulated: int, remaining: int):
        """Update the timer display on the main thread."""
        self._timer_label.set_label(format_duration(accumulated))
        self._remaining_label.set_label(format_minutes_remaining(remaining))
        self._progress_bar.set_fraction(self._tracker.progress)
        return False

    def _update_state_display(self, state: TrackerState):
        """Update UI to reflect the current tracker state."""
        state_config = {
            TrackerState.TRACKING: ("●", "Tracking", "status-dot-active", "Pause tracking"),
            TrackerState.IDLE: ("○", "Idle", "status-dot-idle", "Pause tracking"),
            TrackerState.PAUSED: ("○", "Paused", "status-dot-paused", "Resume tracking"),
            TrackerState.BREAK: ("●", "On a break", "status-dot-break", "Pause tracking"),
            TrackerState.SNOOZED: ("○", "Snoozed", "status-dot-snoozed", "Pause tracking"),
        }

        dot, label, css_class, button_label = state_config.get(
            state,
            ("●", "Tracking", "status-dot-active", "Pause tracking")
        )

        self._status_dot.set_label(dot)
        self._status_label.set_label(label)
        self._pause_button.set_label(button_label)

        # Update CSS classes on the dot
        for cls in ["status-dot-active", "status-dot-idle",
                     "status-dot-paused", "status-dot-break",
                     "status-dot-snoozed"]:
            self._status_dot.remove_css_class(cls)
        self._status_dot.add_css_class(css_class)

        return False

    def _on_pause_clicked(self, button):
        """Toggle pause/resume."""
        if self._tracker.state == TrackerState.PAUSED:
            self._tracker.resume()
        else:
            self._tracker.pause()

    def _on_break_clicked(self, button):
        """Trigger a manual break."""
        self._tracker.force_reminder()
