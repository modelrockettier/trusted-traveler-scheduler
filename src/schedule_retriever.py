import logging
import sqlite3
from time import sleep

from typing import List

from .schedule import Schedule

from .notification_handler import NotificationHandler
import requests
from datetime import datetime

from .config import Config

GOES_URL_FORMAT = "https://ttp.cbp.dhs.gov/schedulerapi/slots?orderBy=soonest&limit=500&locationId={0}&minimum=1"


class ScheduleRetriever:
    """
    A class for retrieving schedules for a given location ID and evaluating available appointment times.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.notification_handler = NotificationHandler(self)
        self.log = logging.getLogger("schedule_retriever")

    def _evaluate_timestamp(
        self, schedule: List[Schedule], location_id: int, timestamp: str
    ) -> List[Schedule]:
        """
        Evaluates the given timestamp against the provided schedule and location ID. If the timestamp is within the
        acceptable range specified in the configuration, it is added to the schedule.

        :param schedule: The current schedule to evaluate the timestamp against.
        :type schedule: List[Schedule]
        :param location_id: The ID of the location to evaluate the timestamp for.
        :type location_id: int
        :param timestamp: The timestamp to evaluate.
        :type timestamp: str
        :return: The updated schedule.
        :rtype: List[Schedule]
        """
        parsed_date = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M")

        for dates in schedule:
            if dates.appointment_date.date() == parsed_date.date():
                if self._is_acceptable_appointment(location_id, parsed_date):
                    dates.appointment_times.append(parsed_date)
                return schedule

        if self._is_acceptable_appointment(location_id, parsed_date):
            schedule.append(Schedule(parsed_date, [parsed_date]))

        return schedule

    def _is_acceptable_appointment(
        self, location_id: int, parsed_date: datetime
    ) -> bool:
        """
        Determines if the given appointment time is acceptable based on the configuration settings and existing
        appointments in the database.

        :param location_id: The ID of the location to check the appointment time for.
        :type location_id: int
        :param parsed_date: The parsed datetime object representing the appointment time.
        :type parsed_date: datetime
        :return: True if the appointment time is acceptable, False otherwise.
        :rtype: bool
        """
        if not self.config.is_date_acceptable(parsed_date):
            return False

        conn = sqlite3.connect("ttp.db")

        cursor = conn.cursor()

        # Check if there is an existing appointment with the same location ID and timestamp
        cursor.execute(
            """SELECT COUNT(*) FROM appointments
                        WHERE location_id = ? AND start_time = ?""",
            (location_id, parsed_date.isoformat()),
        )

        count = cursor.fetchone()[0]

        if count > 0:
            conn.close()

            return False

        cursor.execute(
            """INSERT INTO appointments (location_id, start_time)
                        VALUES (?, ?)""",
            (location_id, parsed_date.isoformat()),
        )

        conn.commit()

        conn.close()

        return True

    def _clear_database_of_claimed_appointments(
        self, location_id: int, all_active_appointments: List
    ) -> None:
        """
        Clears the database of any appointments that have been claimed.

        :return: None
        """
        conn = sqlite3.connect("ttp.db")
        cursor = conn.cursor()

        cursor.execute(
            f"""DELETE FROM appointments
                        WHERE location_id = ? AND start_time NOT IN ({",".join(['?'] * len(all_active_appointments))})""",
            [location_id] + all_active_appointments,
        )

        if cursor.rowcount > 0:
            self.log.info(f"Removed {cursor.rowcount} appointments that have been claimed for location {location_id}.\n")

        conn.commit()
        conn.close()

    def _get_schedule(self, location_id: int) -> None:
        """
        Retrieves the schedule for the given location ID and evaluates the available appointment times. If there are
        any new appointments that meet the criteria specified in the configuration, a notification is sent.

        :param location_id: The ID of the location to retrieve the schedule for.
        :type location_id: int
        :return: None
        """
        try:
            sleep(1)
            response = requests.get(
                GOES_URL_FORMAT.format(location_id), timeout=30
            )
        except OSError:
            if self.log.isEnabledFor(logging.DEBUG):
                self.log.exception("Got OSError")
            return

        if 400 <= response.status_code < 500:
            raise PermissionError(f"API Returned HTTP {response.status_code}")

        try:
            appointments = response.json()
            if not appointments:
                self._clear_database_of_claimed_appointments(location_id, [])
                self.log.info(f"No active appointments available for location {location_id}.")
                return

            self.log.debug(f"{len(appointments)} total appointments")
            schedule = []
            all_active_appointments = []
            for appointment in appointments:
                if appointment["active"]:
                    schedule = self._evaluate_timestamp(
                        schedule, location_id, appointment["startTimestamp"]
                    )
                    all_active_appointments.append(datetime.strptime(appointment["startTimestamp"], "%Y-%m-%dT%H:%M").isoformat())

            self.log.debug(f"{len(all_active_appointments)} acceptable appointments")
            self._clear_database_of_claimed_appointments(location_id, all_active_appointments)

            if not schedule:
                return

            self.notification_handler.new_appointment(location_id, schedule)

        except OSError:
            if self.log.isEnabledFor(logging.DEBUG):
                self.log.exception("Got OSError")

    def monitor_location(self, location_id: int) -> None:
        """
        Monitors the given location ID for available appointment times. If the retrieval interval is set to 0, the
        schedule is retrieved once and the method returns. Otherwise, the method continuously retrieves the schedule
        at the specified interval until the program is terminated.

        :param location_id: The ID of the location to monitor.
        :type location_id: int
        :return: None
        """
        if self.config.retrieval_interval == 0:
            self._get_schedule(location_id)
            return

        while True:
            time_before = datetime.utcnow()

            self._get_schedule(location_id)

            # Account for the time it takes to retrieve the location when
            # deciding how long to sleep
            time_after = datetime.utcnow()
            time_taken = (time_after - time_before).total_seconds()
            time_to_sleep = self.config.retrieval_interval - time_taken
            if time_to_sleep > 0:
                sleep(time_to_sleep)
