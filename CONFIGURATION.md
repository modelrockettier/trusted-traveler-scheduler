# Configuration
This guide contains all the information you need to configure `trusted-traveler-scheduler` to your specifications. An example file of the configuration can be found at [config.example.json](config.example.json).

## Table of Contents

- [Current Appointment Date](#current-appointment-date)
- [Travel Time](#travel-time)
- [Locations](#locations)
- [Notifications](#notifications)
  - [Notification Level](#notification-level)
  - [Notification URLs](#notification-urls)
  - [Test Notifications](#test-notifications)
- [Retrieval Interval](#retrieval-interval)
- [Appointment Times](#appointment-times)
  - [Start Appointment Time](#start-appointment-time)
  - [End Appointment Time](#end-appointment-time)
- [Database](#database)

## Current Appointment Date

Default: None

Type: String

This represents the date of your current appointment if you have one. If you do not have one, leave it as an empty string. This value is used to determine whether to notify you if a new appointment is found. If it is later than your current appointment date, it will not notify you.

```json
{
	"current_appointment_date": "January 1, 2024"
}
```

This above configuration will notify you if a new appointment is found for December 1, 2023, but will not notify you if an appointment is found for January 2, 2024.

**Note:** This must be in the format of Month Day, Year (e.g. January 1, 2024).

## Travel Time
Default: 15 minutes

Type: String

This configuration represents the soonest appointment you would like to be notified about.

```json
{
    "travel_time": "15m"
}
```

## Locations

Default: []

Type: Comma Seperated List or Integer

This represents the IDs of the enrollment centers you wish to monitor. This can either be a list of locations, or a singular location represented by an integer. This list is used in addition to whatever arguments you pass in at run-time of the script. For more information on locations, please see [LOCATIONS.md](LOCATIONS.md).

```json
{
  "location_ids": [ 5140,5444 ]
}
```

or

```json
{
    "location_ids": 5140
}
```

## Notifications

### Notification Level
Default: 1

Type: Integer

This indicates the notification sensitivity you wish to receive. 
```json
{
  "notification_level": 1
}
```
Level 1 means you receive notifications when new appointments are found.

Level 2 means you receive notifications only when errors occur.

### Notification URLs

Default: []

Type: List or String

This uses the [Apprise Library][0] to generate notifications that are pushed to you based on the notification level you have elected to receive. You can find more information about notifications through the [Apprise README.md][1]

```json
{
  "notification_urls": "service://my_service_url"
}
```

or

```json
{
  "notification_urls": [
    "service://my_first_service_url",
    "service://my_second_service_url"
  ]
}
```

### Test Notifications
To test your notification configuration, run the following command:
```shell
python ttp.py -t
```

## Retrieval Interval
Default: 5 minutes

Type: String

This indicates how often the script will fetch new appointments from the monitored locations. To disable automatic retrieval, set this to "0m".

```json
{
    "retrieval_interval": "5m"
}
```

## Appointment Times

### Start Appointment Time
Default: 00:00

Type: String

This indicates the earliest appointment you would like to be notified for. To be notified for all appointments, set this to "00:00".

```json
{
    "start_appointment_time": "06:00"
}
```

### End Appointment Time
Default: 23:59

Type: String

This indicates the latest appointment you would like to be notified for. To be notified for all appointments, set this to "23:59".

```json
{
    "end_appointment_time": "20:00"
}
```

## Database
Default: "ttp.db"

Type: String

The sqlite3 database to store appointments to prevent duplicate notifications.

```json
{
    "database": "ttp.db"
}
```



[0]: https://github.com/caronc/apprise
[1]: https://github.com/caronc/apprise#supported-notifications
