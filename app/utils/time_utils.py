"""Time formatting utilities for Efsal."""


def format_duration(total_seconds: int) -> str:
    """Format seconds into MM:SS display string.

    Args:
        total_seconds: Total number of seconds to format.

    Returns:
        Formatted string like '32:17'.
    """
    if total_seconds < 0:
        total_seconds = 0
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def format_minutes_remaining(seconds_remaining: int) -> str:
    """Format remaining seconds into a human-friendly string.

    Args:
        seconds_remaining: Seconds until next break.

    Returns:
        Human-readable string like '13 minutes until your next break'.
    """
    if seconds_remaining <= 0:
        return "Break time!"

    minutes = seconds_remaining // 60
    if seconds_remaining % 60 > 30:
        minutes += 1

    if minutes <= 0:
        return "Less than a minute until your next break"
    elif minutes == 1:
        return "1 minute until your next break"
    else:
        return f"{minutes} minutes until your next break"


def format_active_short(total_seconds: int) -> str:
    """Format active time as short string for indicator.

    Args:
        total_seconds: Total active seconds.

    Returns:
        Short string like '32m' or '1h 5m'.
    """
    if total_seconds < 60:
        return "< 1m"

    minutes = total_seconds // 60
    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours > 0:
        if remaining_minutes > 0:
            return f"{hours}h {remaining_minutes}m"
        return f"{hours}h"
    return f"{minutes}m"


def seconds_to_minutes(seconds: int) -> int:
    """Convert seconds to whole minutes, rounding up."""
    return (seconds + 59) // 60
