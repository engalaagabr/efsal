"""Application-wide constants for Efsal."""

APP_ID = "io.github.efsal"
APP_NAME = "Efsal"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "A calm reminder to move, stretch, and hydrate"

# Default timer settings (in seconds)
DEFAULT_REMINDER_INTERVAL = 45 * 60  # 45 minutes
DEFAULT_SNOOZE_DURATION = 5 * 60      # 5 minutes
DEFAULT_BREAK_COUNTDOWN = 60          # 1 minute break timer

# Idle detection threshold (in seconds)
# If idle for more than this, consider user away
IDLE_THRESHOLD = 120  # 2 minutes

# Polling interval for idle detection (in milliseconds)
IDLE_POLL_INTERVAL = 5000  # Check every 5 seconds

# Timer update interval for UI (in milliseconds)
UI_UPDATE_INTERVAL = 1000  # Update every second

# Preset reminder intervals (in minutes)
REMINDER_PRESETS = [15, 30, 45, 60, 90]

# Preset snooze durations (in minutes)
SNOOZE_PRESETS = [5, 10, 15]

# D-Bus constants for idle detection
MUTTER_IDLE_MONITOR_BUS = "org.gnome.Mutter.IdleMonitor"
MUTTER_IDLE_MONITOR_PATH = "/org/gnome/Mutter/IdleMonitor/Core"
MUTTER_IDLE_MONITOR_IFACE = "org.gnome.Mutter.IdleMonitor"

# Fallback: GNOME ScreenSaver
SCREENSAVER_BUS = "org.gnome.ScreenSaver"
SCREENSAVER_PATH = "/org/gnome/ScreenSaver"
SCREENSAVER_IFACE = "org.gnome.ScreenSaver"

# Login Manager for sleep/suspend detection
LOGIN_MANAGER_BUS = "org.freedesktop.login1"
LOGIN_MANAGER_PATH = "/org/freedesktop/login1"
LOGIN_MANAGER_IFACE = "org.freedesktop.login1.Manager"

# Config directory
CONFIG_DIR_NAME = "efsal"
CONFIG_FILE_NAME = "settings.json"

# XDG autostart
AUTOSTART_DESKTOP_FILENAME = "io.github.efsal.desktop"

# Break messages - friendly, rotating
BREAK_TITLES = [
    "Time to move a little",
    "Your body says thanks",
    "Quick stretch?",
    "Pause and breathe",
    "Recharge moment",
]

BREAK_MESSAGES = [
    "Stand up, stretch your back, and drink some water.",
    "Roll your shoulders and take a few deep breaths.",
    "Look away from the screen and rest your eyes.",
    "Walk around for a moment — your body will thank you.",
    "Stretch your neck and wrists. Stay hydrated!",
]

BREAK_TIPS = [
    "Stand up",
    "Stretch your back",
    "Roll your shoulders",
    "Drink some water",
    "Look away from the screen",
    "Take a few deep breaths",
    "Walk around briefly",
    "Stretch your wrists",
    "Rest your eyes",
]
