"""Notification service for GNOME desktop notifications."""

from typing import Optional

from gi.repository import Gio, GLib

from app.utils.constants import APP_ID, BREAK_TITLES, BREAK_MESSAGES


class NotificationService:
    """Handles GNOME desktop notifications for break reminders.

    Uses Gio.Notification which integrates natively with GNOME Shell.
    """

    def __init__(self, application: Gio.Application):
        self._app = application
        self._message_index = 0

    def send_break_reminder(self, active_minutes: int):
        """Send a break reminder notification.

        Args:
            active_minutes: How many minutes the user has been active.
        """
        title = BREAK_TITLES[self._message_index % len(BREAK_TITLES)]
        message = (
            f"You've been active for {active_minutes} minutes. "
            f"{BREAK_MESSAGES[self._message_index % len(BREAK_MESSAGES)]}"
        )
        self._message_index += 1

        notification = Gio.Notification.new(title)
        notification.set_body(message)
        notification.set_priority(Gio.NotificationPriority.HIGH)

        # Add actions
        notification.add_button("I'm up", "app.break-acknowledge")
        notification.add_button("Remind me later", "app.break-snooze")

        # Set default action — clicking the notification itself
        notification.set_default_action("app.break-acknowledge")

        self._app.send_notification("break-reminder", notification)

    def withdraw_reminder(self):
        """Remove the break reminder notification."""
        self._app.withdraw_notification("break-reminder")

    def send_simple(self, title: str, body: str):
        """Send a simple informational notification.

        Args:
            title: Notification title.
            body: Notification body text.
        """
        notification = Gio.Notification.new(title)
        notification.set_body(body)
        notification.set_priority(Gio.NotificationPriority.NORMAL)
        self._app.send_notification("info", notification)
