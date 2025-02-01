import json
import logging
import os
import re
import sys
from typing import Any, Dict
from datetime import datetime, date, time, timedelta

from .notification_level import NotificationLevel

CONFIG_FILE_NAME = "config.json"
LOCATION_FILE_NAME = "locations.json"

class Config:
    """
    A class representing the configuration for the Trusted Traveler Scheduler application.
    """
    def __init__(self):
        # Default values are set
        self.current_appointment_date = None
        self.travel_time = 900 # 15 minutes
        self.database = 'ttp.db'
        self.location_ids = []
        self.notification_level = NotificationLevel.INFO
        self.notification_urls = []
        self.retrieval_interval = 300
        self.start_appointment_time = None
        self.end_appointment_time = None

        # Read the config file
        config = self._get_config()
        self.locations = self._get_locations()

        # Set the configuration values if provided
        try:
            self._parse_config(config)
        except TypeError as err:
            log = logging.getLogger("config")
            log.exception("Error in configuration file:")
            sys.exit()

    def _get_config(self) -> Dict[str, Any]:
        """
        Reads the configuration file and returns its contents as a dictionary.

        Returns:
            A dictionary containing the configuration values.
        """
        project_dir = os.path.dirname(os.path.dirname(__file__))
        config_file = project_dir + "/" + CONFIG_FILE_NAME

        config = {}
        try:
            with open(config_file) as file:
                config = json.load(file)
        except FileNotFoundError:
            pass

        return config

    def _get_locations(self) -> Dict[str, Any]:
        """
        Reads the locations file and returns its contents as a dictionary.

        Returns:
            A dictionary containing the locations.
        """
        project_dir = os.path.dirname(os.path.dirname(__file__))
        locations_file = project_dir + "/utils/" + LOCATION_FILE_NAME

        locations = {}
        try:
            with open(locations_file, encoding="utf-8") as file:
                locations = json.load(file)
        except FileNotFoundError:
            pass

        return locations

    # This method ensures the configuration values are correct and the right types.
    # Defaults are already set in the constructor to ensure a value is never null.
    def _parse_config(self, config: Dict[str, Any]) -> None:
        """
        Parses the configuration dictionary and sets the corresponding attributes of the Config object.

        Args:
            config: A dictionary containing the configuration values.

        Raises:
            TypeError: If any of the configuration values are of the wrong type.
            ValueError: If any of the configuration values are invalid.
        """
        conversions = {
            'current_appointment_date': self.convert_to_date,
            'notification_level': int,
            'retrieval_interval': self.convert_to_seconds,
            'start_appointment_time': self.convert_to_time,
            'end_appointment_time': self.convert_to_time,
            'travel_time': self.convert_to_seconds,
            'database': str,
        }
        for key, func in conversions.items():
            value = config.get(key)
            if value is not None:
                setattr(self, key, func(value))

        if "location_ids" in config:
            if isinstance(config["location_ids"], (int, str)):
                self.location_ids = [config["location_ids"]]
            elif isinstance(config["location_ids"], list):
                self.location_ids = config["location_ids"]
            else:
                raise TypeError("'location_ids' must be a list or integer")

        if "notification_urls" in config:
            if isinstance(config["notification_urls"], str):
                self.notification_urls = [config["notification_urls"]]
            elif isinstance(config["notification_urls"], list):
                self.notification_urls = config["notification_urls"]
            else:
                raise TypeError("'notification_urls' must be a list or string")

    def validate(self):
        if self.current_appointment_date and self.current_appointment_date < date.today():
            raise TypeError("'current_appointment_date' cannot be in the past")

        if (self.start_appointment_time and self.end_appointment_time and
            self.start_appointment_time > self.end_appointment_time):
            raise TypeError("'start_appointment_time' cannot be after 'end_appointment_time'")

        # Sort and unique-ify location_ids
        self.location_ids = sorted(set(self.location_ids))
        # Unique-ify notification_urls, but maintain ordering on Python 3.7+
        self.notification_urls = list(dict.fromkeys(self.notification_urls))

    @staticmethod
    def convert_to_seconds(duration: str | int) -> int:
        """
        Converts a duration string to seconds.

        Args:
            duration: A string representing a time interval in the format of <integer><unit>. (e.g. 45s (seconds), 30m (minutes), 2h (hours), 1d (days))

        Returns:
            An integer representing the time interval in seconds.

        Raises:
            ValueError: If the duration string is not in the correct format or contains an invalid time unit.
        """
        # If the time is already an integer, return it
        try:
            return int(duration)
        except:
            pass

        match = re.match(r'^(\d+)([smhd])$', duration.lower())

        if not match:
            raise ValueError(f"must be in the format of <integer><unit>. (e.g. 45s (seconds), 30m (minutes), 2h (hours), 1d (days))")

        value, unit = int(match.group(1)), match.group(2)

        if unit == "s":
            return value
        elif unit == "m":
            return value * 60
        elif unit == "h":
            return value * 3600
        elif unit == "d":
            return value * 86400
        else:
            raise ValueError(f"invalid time unit: {unit}. Accepted units: s (seconds), m (minutes), h (hours), d (days).")

    @staticmethod
    def convert_to_date(dateStr: str | date) -> date:
        """
        Converts a date string to a datetime.date object.

        Args:
            dateStr: A string representing a date in the format of HH:MM.

        Returns:
            A date object representing the date.

        Raises:
            ValueError: If the date string is not in the correct format.
        """
        # If the dateStr is already a date, return it
        try:
            return date(dateStr)
        except:
            pass

        try:
            return datetime.strptime(dateStr, '%B %d, %Y').date()
        except Exception:
            raise ValueError("date must be in the format of Month Day, Year (e.g. January 1, 2024)")

    @staticmethod
    def convert_to_time(timeStr: str | time) -> time:
        """
        Converts a time string to a datetime.time object.

        Args:
            timeStr: A string representing a time in the format of HH:MM.

        Returns:
            A time object representing the time.

        Raises:
            ValueError: If the time string is not in the correct format.
        """
        # If the timeStr is already a time, return it
        try:
            return time(timeStr)
        except:
            pass

        try:
            return datetime.strptime(timeStr, "%H:%M").time()
        except Exception:
            raise ValueError("time must be in the format of HH:MM (e.g. 15:00)")

    def is_date_acceptable(self, when: datetime) -> bool:
        """
        Returns whether an appointment date is acceptable.

        Args:
            when: The appointment date

        Returns:
            True if the appointment date is acceptable, otherwise False.

        Raises:
            None
        """
        if (
            self.current_appointment_date is not None
            and when.date() >= self.current_appointment_date
        ):
            return False

        if (
            self.travel_time is not None
            and when < datetime.now() + timedelta(seconds=self.travel_time)
        ):
            return False

        if (
            self.start_appointment_time is not None
            and when.time() < self.start_appointment_time
        ):
            return False

        if (
            self.end_appointment_time is not None
            and when.time() > self.end_appointment_time
        ):
            return False

        return True
