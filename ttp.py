#!/usr/bin/env python3
"""Entrypoint into the script where the arguments are passed to src.main"""

import argparse
import logging
import sys

from datetime import datetime
from src.config import Config
from src.main import main
from src.schedule_retriever import ScheduleRetriever

__version__ = "1.3.0"

def add_arguments(parser: argparse.ArgumentParser):
    parser.add_argument('-v', '--version',
                        action='version',
                        version=f'%(prog)s {__version__}',
                        help='show the current version and exit')

    parser.add_argument('-t', '--test-notifications',
                        action='store_true',
                        help='test the notification and exit')

    parser.add_argument('-d', '--current-appointment-date',
                        type=str,
                        help='Current appointment date in the format "Month Day, Year" (e.g. "December 31, 2023")')

    parser.add_argument('-l', '--location-ids',
                        type=str,
                        help='Comma-separated list of location IDs (e.g. 1020,1030)')

    parser.add_argument('-n', '--notification-level',
                        type=int,
                        help='Notification level (e.g. 1)')

    parser.add_argument('-u', '--notification-urls',
                        type=str,
                        help='Comma-separated list of notification URLs in the Apprise format (e.g. discord://id/token,discord://id/token)')

    parser.add_argument('-r', '--retrieval-interval',
                        type=str,
                        help='Retrieval interval in specified unit (e.g. 5m)')

    parser.add_argument('-s', '--start-appointment-time',
                        type=str,
                        help='The earliest appointment time you would like to be notified for in HH:MM format (e.g. 08:00)')

    parser.add_argument('-e', '--end-appointment-time',
                        type=str,
                        help='The latest appointment time you would like to be notified for in in HH:MM format (e.g. 17:00)')

    parser.add_argument('-T', '--travel-time',
                        type=str,
                        help='Only consider appointments at least this amount of time from now (default: 15m)')

    parser.add_argument('-D', '--debug',
                        action='store_true',
                        help='Log debug messages')

def config_from_arguments(args):
    log = logging.getLogger()
    if args.debug:
        log.setLevel(logging.DEBUG)

    if args.current_appointment_date:
        config.current_appointment_date = datetime.strptime(args.current_appointment_date, '%B %d, %Y')
        if config.current_appointment_date < datetime.now():
            raise TypeError("'current_appointment_date' cannot be in the past")

    if args.location_ids:
        location_ids = [int(x) for x in args.location_ids.split(',')]
        for location_id in location_ids:
            if location_id not in config.location_ids:
                config.location_ids.append(location_id)

    if args.notification_level:
        config.notification_level = args.notification_level

    if args.notification_urls:
        notification_urls = args.notification_urls.split(',')
        for notification_url in notification_urls:
            if notification_url not in config.notification_urls:
                config.notification_urls.append(notification_url)

    if args.retrieval_interval:
        try:
            config.retrieval_interval = config.convert_to_seconds(args.retrieval_interval)
        except ValueError as err:
                raise TypeError(err)

    if args.start_appointment_time:
        try:
            config.start_appointment_time = config.convert_to_datetime(args.start_appointment_time)
        except ValueError as err:
                raise TypeError(err)

    if args.end_appointment_time:
        try:
            config.end_appointment_time = config.convert_to_datetime(args.end_appointment_time)
        except ValueError as err:
                raise TypeError(err)

    if args.travel_time:
        try:
            config.travel_time = config.convert_to_seconds(args.travel_time)
        except ValueError as err:
                raise TypeError(err)

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

    try:
        main(config)
    except KeyboardInterrupt:
        print("") # print newline first
        log.info("Ctrl+C pressed. Stopping all checkins")
        sys.exit()
