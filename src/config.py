import json
import logging
import os
import re
import sys
from typing import Any, Dict
from datetime import datetime, timedelta

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
        self.start_appointment_time = datetime(year=9999, month=12, day=31, hour=0, minute=0)
        self.end_appointment_time = datetime(year=9999, month=12, day=31, hour=23, minute=59)

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
        if config.get("current_appointment_date"):
            self.current_appointment_date = config["current_appointment_date"]

            try:
                self.current_appointment_date = datetime.strptime(self.current_appointment_date, '%B %d, %Y')
            except:
                raise TypeError("'current_appointment_date' must be in the format of Month Day, Year (e.g. January 1, 2024)")

            if self.current_appointment_date < datetime.now():
                raise TypeError("'current_appointment_date' cannot be in the past")

        if "location_ids" in config:
            self.location_ids = config["location_ids"]

            if not isinstance(self.location_ids, (list, int)):
                raise TypeError("'location_ids' must be a list or integer")

        if "notification_level" in config:
            self.notification_level = config["notification_level"]

            if not isinstance(self.notification_level, int):
                raise TypeError("'notification_level' must be an integer")

        if "notification_urls" in config:
            self.notification_urls = config["notification_urls"]

            if not isinstance(self.notification_urls, (list, str)):
                raise TypeError("'notification_urls' must be a list or string")

        if "retrieval_interval" in config:
            self.retrieval_interval = config["retrieval_interval"]

            if not isinstance(self.retrieval_interval, str):
                raise TypeError("'retrieval_interval' must be a string")

            try:
                self.retrieval_interval = self.convert_to_seconds(self.retrieval_interval)
            except ValueError as err:
                raise TypeError(err)

        if "start_appointment_time" in config:
            self.start_appointment_time = config["start_appointment_time"]

            if not isinstance(self.start_appointment_time, str):
                raise TypeError("'start_appointment_time' must be a string")

            try:
                self.start_appointment_time = self.convert_to_datetime(self.start_appointment_time)
            except ValueError as err:
                raise TypeError(err)

        if "end_appointment_time" in config:
            self.end_appointment_time = config["end_appointment_time"]

            if not isinstance(self.end_appointment_time, str):
                raise TypeError("'end_appointment_time' must be a string")

            try:
                self.end_appointment_time = self.convert_to_datetime(self.end_appointment_time)
            except ValueError as err:
                raise TypeError(err)

        if "travel_time" in config:
            self.travel_time = config["travel_time"]

            if not isinstance(self.travel_time, str):
                raise TypeError("'travel_time' must be a string")

            self.travel_time = self.convert_to_seconds(self.travel_time)

        if "database" in config:
            self.database = config["database"]

    def convert_to_seconds(self, time: str) -> int:
        """
        Converts a time string to seconds.

        Args:
            time: A string representing a time interval in the format of <integer><unit>. (e.g. 45s (seconds), 30m (minutes), 2h (hours), 1d (days))

        Returns:
            An integer representing the time interval in seconds.

        Raises:
            ValueError: If the time string is not in the correct format or contains an invalid time unit.
        """
        # If the time is already an integer, return it
        try:
            return int(time)
        except:
            pass

        match = re.match(r'^(\d+)([smhd])$', time.lower())

        if not match:
            raise ValueError(f"'retrieval_interval' must be in the format of <integer><unit>. (e.g. 45s (seconds), 30m (minutes), 2h (hours), 1d (days))")

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
            raise ValueError(f"'retrieval_interval' invalid time unit: {unit}. Accepted units: s (seconds), m (minutes), h (hours), d (days).")

    def convert_to_datetime(self, time: str) -> datetime:
        """
        Converts a time string to a datetime object.

        Args:
            time: A string representing a time in the format of HH:MM.

        Returns:
            A datetime object representing the time.

        Raises:
            ValueError: If the time string is not in the correct format.
        """
        return datetime.strptime(time, "%H:%M")

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
            and when >= self.current_appointment_date
        ):
            return False

        if (
            self.travel_time is not None
            and when < datetime.now() + timedelta(seconds=self.travel_time)
        ):
            return False

        if (
            self.start_appointment_time is not None
            and when.time() < self.start_appointment_time.time()
        ):
            return False

        if (
            self.end_appointment_time is not None
            and when.time() > self.end_appointment_time.time()
        ):
            return False

        return True
