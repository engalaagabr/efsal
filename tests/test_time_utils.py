"""Tests for time_utils module."""

import unittest

from app.utils.time_utils import (
    format_duration,
    format_minutes_remaining,
    format_active_short,
    seconds_to_minutes,
)


class TestFormatDuration(unittest.TestCase):
    """Tests for format_duration()."""

    def test_zero(self):
        self.assertEqual(format_duration(0), "00:00")

    def test_seconds_only(self):
        self.assertEqual(format_duration(45), "00:45")

    def test_minutes_and_seconds(self):
        self.assertEqual(format_duration(125), "02:05")

    def test_large_value(self):
        self.assertEqual(format_duration(3661), "61:01")

    def test_exact_minute(self):
        self.assertEqual(format_duration(300), "05:00")

    def test_negative(self):
        self.assertEqual(format_duration(-10), "00:00")

    def test_45_minutes(self):
        self.assertEqual(format_duration(2700), "45:00")


class TestFormatMinutesRemaining(unittest.TestCase):
    """Tests for format_minutes_remaining()."""

    def test_zero(self):
        self.assertEqual(format_minutes_remaining(0), "Break time!")

    def test_negative(self):
        self.assertEqual(format_minutes_remaining(-5), "Break time!")

    def test_one_minute(self):
        result = format_minutes_remaining(60)
        self.assertIn("1 minute", result)

    def test_multiple_minutes(self):
        result = format_minutes_remaining(780)
        self.assertIn("13 minutes", result)

    def test_less_than_minute(self):
        result = format_minutes_remaining(25)
        self.assertIn("Less than a minute", result)


class TestFormatActiveShort(unittest.TestCase):
    """Tests for format_active_short()."""

    def test_less_than_minute(self):
        self.assertEqual(format_active_short(30), "< 1m")

    def test_minutes(self):
        self.assertEqual(format_active_short(1920), "32m")

    def test_hours(self):
        self.assertEqual(format_active_short(3600), "1h")

    def test_hours_and_minutes(self):
        self.assertEqual(format_active_short(3900), "1h 5m")


class TestSecondsToMinutes(unittest.TestCase):
    """Tests for seconds_to_minutes()."""

    def test_exact(self):
        self.assertEqual(seconds_to_minutes(120), 2)

    def test_round_up(self):
        self.assertEqual(seconds_to_minutes(121), 3)

    def test_zero(self):
        self.assertEqual(seconds_to_minutes(0), 0)


if __name__ == "__main__":
    unittest.main()
