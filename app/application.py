"""Efsal — main Adw.Application class.

Coordinates all services, handles application lifecycle,
and manages window creation and actions.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio, GLib, Gdk

from app.models.settings import Settings
from app.services.idle_detector import IdleDetector
from app.services.activity_tracker import ActivityTracker, TrackerState
from app.services.notification_service import NotificationService
from app.ui.main_window import MainWindow
from app.ui.break_popup import BreakPopup, ManualBreakPopup
from app.ui.preferences import PreferencesWindow
from app.utils.constants import APP_ID, APP_NAME, APP_VERSION


class EfsalApp(Adw.Application):
    """The main application object for Efsal.

    Handles application lifecycle, coordinates services,
    and manages windows and actions.
    """

    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self._settings: Settings = None
        self._idle_detector: IdleDetector = None
        self._tracker: ActivityTracker = None
        self._notification_service: NotificationService = None
        self._main_window: MainWindow = None
        self._break_popup: BreakPopup = None
        self._css_loaded = False

    def do_startup(self):
        """Called once when the application starts."""
        Adw.Application.do_startup(self)
        self.hold()  # Keep application running in background

        # Initialize services
        self._settings = Settings()
        self._idle_detector = IdleDetector()
        self._tracker = ActivityTracker(self._settings, self._idle_detector)
        self._notification_service = NotificationService(self)

        # Set up tracker callbacks
        self._tracker.on_threshold_reached = self._on_break_time

        # Apply theme from settings
        self._apply_theme()

        # Register actions
        self._setup_actions()

    def do_activate(self):
        """Called when the application is activated (window shown)."""
        if not self._css_loaded:
            self._load_css()
            self._css_loaded = True

        if not self._main_window:
            self._main_window = MainWindow(self, self._tracker)
            self._tracker.start()

        self._main_window.present()

    def do_shutdown(self):
        """Called when the application is shutting down."""
        if self._tracker:
            self._tracker.stop()
        if self._settings:
            self._settings.save()
        Adw.Application.do_shutdown(self)

    def _setup_actions(self):
        """Register application-level GActions."""
        actions = {
            "preferences": self._on_preferences,
            "about": self._on_about,
            "quit": self._on_quit,
            "reset-timer": self._on_reset_timer,
            "break-acknowledge": self._on_break_acknowledge,
            "break-snooze": self._on_break_snooze,
            "take-break": self._on_take_break,
            "pause": self._on_pause_action,
            "resume": self._on_resume_action,
        }

        for name, callback in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)

    def _load_css(self):
        """Load custom CSS for the application."""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_string(self._get_css())
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

    def _get_css(self) -> str:
        """Return the application CSS string."""
        return """
        .timer-display {
            font-size: 72px;
            font-weight: 200;
            font-feature-settings: "tnum";
            letter-spacing: -2px;
            margin-top: 16px;
            margin-bottom: 8px;
            color: @theme_fg_color;
        }

        .timer-card {
            background-color: @card_bg_color;
            border-radius: 24px;
            border: 1px solid alpha(@borders, 0.5);
            padding: 40px 24px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.06);
            margin: 24px 0;
        }

        .break-emoji {
            font-size: 56px;
            margin-bottom: 8px;
        }

        .break-countdown {
            font-size: 42px;
            font-weight: 300;
            font-feature-settings: "tnum";
            color: @accent_color;
        }

        .break-tips {
            font-size: 13px;
            line-height: 1.6;
        }

        .status-dot-active {
            color: @success_color;
            font-size: 12px;
        }

        .status-dot-idle {
            color: @warning_color;
            font-size: 12px;
        }

        .status-dot-paused {
            color: @dim_label_color;
            font-size: 12px;
        }

        .status-dot-break {
            color: @success_color;
            font-size: 12px;
        }

        .status-dot-snoozed {
            color: @warning_color;
            font-size: 12px;
        }

        progressbar trough {
            min-height: 8px;
            border-radius: 4px;
        }

        progressbar progress {
            min-height: 8px;
            min-width: 0px;
            border-radius: 4px;
        }
        """

    def _apply_theme(self):
        """Apply the user's theme preference."""
        style_manager = Adw.StyleManager.get_default()
        schemes = {
            "system": Adw.ColorScheme.DEFAULT,
            "light": Adw.ColorScheme.FORCE_LIGHT,
            "dark": Adw.ColorScheme.FORCE_DARK,
        }
        style_manager.set_color_scheme(
            schemes.get(self._settings.theme, Adw.ColorScheme.DEFAULT)
        )

    def _on_break_time(self):
        """Called when the reminder threshold is reached."""
        active_mins = self._tracker.accumulated_seconds // 60

        # Send notification
        self._notification_service.send_break_reminder(active_mins)

        # Show popup if enabled
        if self._settings.show_popup:
            self._show_break_popup(active_mins)

    def _show_break_popup(self, active_minutes: int):
        """Display the break reminder popup."""
        if self._break_popup:
            self._break_popup.close()

        self._break_popup = BreakPopup(
            application=self,
            active_minutes=active_minutes,
            on_acknowledge=self._handle_acknowledge,
            on_snooze=self._handle_snooze,
        )
        self._break_popup.present()

    def _handle_acknowledge(self):
        """User acknowledged the break reminder."""
        self._notification_service.withdraw_reminder()
        if self._settings.reset_after_reminder:
            self._tracker.reset()
        else:
            self._tracker.end_break()

    def _handle_snooze(self):
        """User snoozed the reminder."""
        self._notification_service.withdraw_reminder()
        self._tracker.snooze()

    # --- Action handlers ---

    def _on_preferences(self, action, param):
        prefs = PreferencesWindow(self, self._settings)
        prefs.present()

    def _on_about(self, action, param):
        about = Adw.AboutWindow(
            application_name=APP_NAME,
            application_icon="preferences-desktop-accessibility-symbolic",
            version=APP_VERSION,
            developer_name="Efsal",
            comments="A calm reminder to move, stretch, and hydrate.\n\n"
                     "Privacy: This app does not record keystrokes, mouse "
                     "movements, or screenshots. It only detects whether "
                     "your system is active or idle.",
            website="https://github.com/efsal/efsal",
            license_type=Gtk.License.MIT_X11,
            transient_for=self._main_window,
            modal=True,
        )
        about.present()

    def _on_quit(self, action, param):
        self.release()  # Release the background hold
        self.quit()

    def _on_reset_timer(self, action, param):
        self._tracker.reset()

    def _on_break_acknowledge(self, action, param):
        self._handle_acknowledge()

    def _on_break_snooze(self, action, param):
        self._handle_snooze()

    def _on_take_break(self, action, param):
        popup = ManualBreakPopup(
            application=self,
            on_done=lambda: self._tracker.reset(),
        )
        popup.present()

    def _on_pause_action(self, action, param):
        self._tracker.pause()

    def _on_resume_action(self, action, param):
        self._tracker.resume()
