"""Idle detection service using GNOME D-Bus APIs.

Supports Wayland and X11 via org.gnome.Mutter.IdleMonitor.
Falls back gracefully if the D-Bus service is unavailable.
"""

import subprocess
from typing import Optional

from gi.repository import Gio, GLib

from app.utils.constants import (
    IDLE_THRESHOLD,
    MUTTER_IDLE_MONITOR_BUS,
    MUTTER_IDLE_MONITOR_IFACE,
    MUTTER_IDLE_MONITOR_PATH,
)


class IdleDetector:
    """Detects user idle state via GNOME Mutter IdleMonitor D-Bus API.

    This works on both Wayland and X11 under GNOME.
    The detector queries the current idle time in milliseconds and
    compares it against the configured threshold.
    """

    def __init__(self, idle_threshold: int = IDLE_THRESHOLD):
        """Initialize the idle detector.

        Args:
            idle_threshold: Seconds of inactivity before considering
                            the user idle.
        """
        self._idle_threshold = idle_threshold
        self._proxy: Optional[Gio.DBusProxy] = None
        self._available = False
        self._last_idle_ms = 0

        self._init_dbus_proxy()

    def _init_dbus_proxy(self):
        """Create a D-Bus proxy to the Mutter IdleMonitor."""
        try:
            self._proxy = Gio.DBusProxy.new_for_bus_sync(
                Gio.BusType.SESSION,
                Gio.DBusProxyFlags.NONE,
                None,
                MUTTER_IDLE_MONITOR_BUS,
                MUTTER_IDLE_MONITOR_PATH,
                MUTTER_IDLE_MONITOR_IFACE,
                None,
            )
            # Test the connection
            result = self._proxy.call_sync(
                "GetIdletime",
                None,
                Gio.DBusCallFlags.NONE,
                1000,
                None,
            )
            if result is not None:
                self._available = True
                print("IdleDetector: Mutter IdleMonitor connected")
            else:
                self._available = False
                print("IdleDetector: Mutter IdleMonitor returned None")
        except GLib.Error as e:
            self._available = False
            print(f"IdleDetector: Mutter IdleMonitor unavailable: {e.message}")
            self._try_fallback()

    def _try_fallback(self):
        """Try fallback idle detection via gdbus command."""
        try:
            result = subprocess.run(
                [
                    "gdbus", "call", "--session",
                    "--dest", MUTTER_IDLE_MONITOR_BUS,
                    "--object-path", MUTTER_IDLE_MONITOR_PATH,
                    "--method", f"{MUTTER_IDLE_MONITOR_IFACE}.GetIdletime",
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                self._available = True
                print("IdleDetector: Fallback gdbus method available")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("IdleDetector: No idle detection available — "
                  "will assume user is always active")

    @property
    def available(self) -> bool:
        """Whether idle detection is working."""
        return self._available

    @property
    def idle_threshold(self) -> int:
        """Idle threshold in seconds."""
        return self._idle_threshold

    @idle_threshold.setter
    def idle_threshold(self, seconds: int):
        """Set idle threshold in seconds."""
        self._idle_threshold = max(10, seconds)

    def get_idle_time_ms(self) -> int:
        """Get current idle time in milliseconds.

        Returns:
            Idle time in milliseconds, or 0 if detection unavailable
            (assumes active).
        """
        if not self._available:
            return 0

        # Try D-Bus proxy first
        if self._proxy is not None:
            try:
                result = self._proxy.call_sync(
                    "GetIdletime",
                    None,
                    Gio.DBusCallFlags.NONE,
                    1000,
                    None,
                )
                if result is not None:
                    idle_ms = result.unpack()[0]
                    self._last_idle_ms = idle_ms
                    return idle_ms
            except GLib.Error:
                pass

        # Fallback to gdbus command
        try:
            result = subprocess.run(
                [
                    "gdbus", "call", "--session",
                    "--dest", MUTTER_IDLE_MONITOR_BUS,
                    "--object-path", MUTTER_IDLE_MONITOR_PATH,
                    "--method", f"{MUTTER_IDLE_MONITOR_IFACE}.GetIdletime",
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                # Output format: (uint64 12345,)
                output = result.stdout.strip()
                idle_ms = int(output.strip("()").split()[1].rstrip(","))
                self._last_idle_ms = idle_ms
                return idle_ms
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass

        return self._last_idle_ms

    def get_idle_time_seconds(self) -> float:
        """Get current idle time in seconds."""
        return self.get_idle_time_ms() / 1000.0

    def is_idle(self) -> bool:
        """Check if user is currently idle.

        Returns:
            True if the user has been idle longer than the threshold.
        """
        return self.get_idle_time_seconds() >= self._idle_threshold

    def is_active(self) -> bool:
        """Check if user is currently active.

        Returns:
            True if the user is actively using the computer.
        """
        return not self.is_idle()
