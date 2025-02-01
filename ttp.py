#!/usr/bin/env python3
"""Entrypoint into the script where the arguments are passed to src.main"""

import argparse
import logging
import sys

from datetime import datetime, date
from src.config import Config
from src.main import main
from src.schedule_retriever import ScheduleRetriever

__version__ = "1.3.0"

def split_ints(values: str):
    """Split a comma-separated string of integers into a list."""
    return [int(x) for x in values.split(',')]

def split_strs(values: str):
    """Split a comma-separated string into a list."""
    return [x for x in values.split(',')]

def add_arguments(parser: argparse.ArgumentParser):
    parser.add_argument('-v', '--version',
                        action='version',
                        version=f'%(prog)s {__version__}',
                        help='show the current version and exit')

    parser.add_argument('-t', '--test-notifications',
                        action='store_true',
                        help='test the notification and exit')

    parser.add_argument('-d', '--current-appointment-date',
                        type=config.convert_to_date,
                        help='Current appointment date in the format "Month Day, Year" (e.g. "December 31, 2023")')

    parser.add_argument('-l', '--location-ids',
                        type=split_ints, action='extend',
                        help='Comma-separated list of location IDs (e.g. 1020,1030)')

    parser.add_argument('-n', '--notification-level',
                        type=int,
                        help='Notification level (e.g. 1)')

    parser.add_argument('-u', '--notification-urls',
                        type=split_strs, action='extend',
                        help='Notification URLs in the Apprise format. May be specified multiple times (e.g. -u discord://id/token -u ntfys://topic/)')

    parser.add_argument('-r', '--retrieval-interval',
                        type=config.convert_to_seconds,
                        help='Retrieval interval in specified unit (e.g. 5m)')

    parser.add_argument('-s', '--start-appointment-time',
                        type=config.convert_to_time,
                        help='The earliest appointment time you would like to be notified for in HH:MM format (e.g. 08:00)')

    parser.add_argument('-e', '--end-appointment-time',
                        type=config.convert_to_time,
                        help='The latest appointment time you would like to be notified for in in HH:MM format (e.g. 17:00)')

    parser.add_argument('-T', '--travel-time',
                        type=config.convert_to_seconds,
                        help='Only consider appointments at least this amount of time from now (default: 15m)')

    parser.add_argument('-D', '--debug',
                        action='store_true',
                        help='Log debug messages')

    parser.add_argument('--database',
                        help='The sqlite3 database to prevent duplicate notifications (default ttp.db)')

def config_from_arguments(args):
    log = logging.getLogger()
    if args.debug:
        log.setLevel(logging.DEBUG)

    fields = (
        'current_appointment_date',
        'location_ids',
        'notification_level',
        'notification_urls',
        'retrieval_interval',
        'start_appointment_time',
        'end_appointment_time',
        'travel_time',
        'database',
    )
    for key in fields:
        value = getattr(args, key, None)
        if value is not None:
            setattr(config, key, value)

    if args.test_notifications:
        schedule_retriever = ScheduleRetriever(config)

        log.info("Sending test notifications...")
        schedule_retriever.notification_handler.send_notification("This is a test message.")
        sys.exit()

if __name__ == "__main__":
    logging.basicConfig(datefmt='%Y/%m/%d %H:%M:%S', format='%(asctime)s: %(message)s',
                        level=logging.INFO)
    config = Config()

    parser = argparse.ArgumentParser(description="Parse command line arguments")
    add_arguments(parser)
    args = parser.parse_args()
    config_from_arguments(args)
    config.validate()

    try:
        main(config)
    except KeyboardInterrupt:
        print("") # print newline first
        log.info("Ctrl+C pressed. Stopping all checkins")
        sys.exit()
