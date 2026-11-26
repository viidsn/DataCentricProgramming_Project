"""Import recorded bus trips into the XAMPP database."""

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

import pymysql

from database import connect_to_database


CSV_PATH = Path(__file__).resolve().parent / "data" / "bus_trips.csv"
COLUMNS = [
    "date", "direction", "stop_name", "scheduled_arrival", "actual_arrival",
    "time_of_day", "destination_arrival", "wait_time", "weather",
]
BOARDING_STOPS = {
    "Athboy to Dublin": "Victorine Abbey",
    "Dublin to Athboy": "Dalymount",
}


def read_trips(path: Path) -> list[tuple]:
    """Read and validate complete trip observations from the CSV."""
    trips = []
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source, strict=True)
        if next(reader, None) != COLUMNS:
            raise ValueError("The CSV headers do not match the trip columns.")

        for row in reader:
            trips.append(parse_trip(row))
    return trips


def parse_trip(row: list[str]) -> tuple:
    """Check a CSV row against the measurement rules in the README."""
    if len(row) != len(COLUMNS):
        raise ValueError(f"expected {len(COLUMNS)} fields, found {len(row)}")
    fields = []
    for field in row:
        value = field.strip()
        if value == "":
            raise ValueError("All trip fields are required")
        fields.append(value)
    trip_date = fields[0]
    direction = fields[1]
    stop = fields[2]
    scheduled = fields[3]
    actual = fields[4]
    period = fields[5]
    destination = fields[6]
    wait = fields[7]
    weather = fields[8]

    parsed_date = date.fromisoformat(trip_date)
    if parsed_date.isoformat() != trip_date:
        raise ValueError("date must use YYYY-MM-DD")
    if BOARDING_STOPS.get(direction) != stop:
        raise ValueError("direction and boarding stop must match")

    scheduled_time = parse_arrival(scheduled)
    actual_time = parse_arrival(actual)
    destination_time = parse_arrival(destination)

    hour = int(scheduled[:2])
    if hour < 12:
        expected_period = "morning"
    elif hour < 17:
        expected_period = "afternoon"
    else:
        expected_period = "evening"
    if period != expected_period:
        raise ValueError("time_of_day must match the scheduled arrival")

    wait_minutes = int(wait)
    if not 0 <= wait_minutes <= 4_294_967_295:
        raise ValueError("wait_time must fit in an unsigned INT")
    if weather not in ("rain", "dry"):
        raise ValueError("weather must be rain or dry")

    return (
        parsed_date, direction, stop, scheduled_time, actual_time,
        period, destination_time, wait_minutes, weather,
    )


def parse_arrival(value: str) -> timedelta:
    """Convert a CSV time to the same format PyMySQL uses for SQL TIME."""
    if len(value) != 5 or not value.isascii():
        raise ValueError("arrival times must use HH:MM")
    arrival = datetime.strptime(value, "%H:%M")
    return timedelta(hours=arrival.hour, minutes=arrival.minute)


def import_trips(connection: pymysql.connections.Connection, trips: list[tuple]) -> int:
    """Insert observations that are not already stored and return the count."""
    select_trips = """
        SELECT `date`, direction, stop_name, scheduled_arrival, actual_arrival,
               time_of_day, destination_arrival, wait_time, weather
        FROM bus_trips
    """
    insert_trip = """
        INSERT INTO bus_trips (
            `date`, direction, stop_name, scheduled_arrival, actual_arrival,
            time_of_day, destination_arrival, wait_time, weather
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    inserted = 0
    with connection.cursor() as cursor:
        cursor.execute(select_trips)
        stored_trips = list(cursor.fetchall())
        for trip in trips:
            if trip not in stored_trips:
                cursor.execute(insert_trip, trip)
                stored_trips.append(trip)
                inserted += 1
    return inserted


def main() -> None:
    """Read the CSV, import new trips, and report how many were added."""
    try:
        trips = read_trips(CSV_PATH)
        with connect_to_database() as connection:
            added = import_trips(connection, trips)
            connection.commit()
    except (ValueError, csv.Error):
        print("Trip import failed: invalid CSV data.")
        return

    print(f"Added {added} trip(s) from {CSV_PATH.name}.")


main()
