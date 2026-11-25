"""Import recorded bus trips into the XAMPP database."""

import csv
from datetime import date, time, timedelta
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
    """Read and validate observations, converting blank fields to None."""
    trips = []
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source, strict=True)
        if next(reader, None) != COLUMNS:
            raise ValueError("The CSV headers do not match the trip columns.")

        for row in reader:
            if not row:
                continue
            try:
                trips.append(parse_trip(row))
            except ValueError as error:
                raise ValueError(f"CSV line {reader.line_num}: {error}") from error
    return trips


def parse_trip(row: list[str]) -> tuple:
    """Check a CSV row against the measurement rules in the README."""
    if len(row) != len(COLUMNS):
        raise ValueError(f"expected {len(COLUMNS)} fields, found {len(row)}")
    fields = [field.strip() for field in row]
    trip_date, direction, stop, scheduled, actual, period, destination, wait, weather = fields

    parsed_date = date.fromisoformat(trip_date)
    if parsed_date.isoformat() != trip_date:
        raise ValueError("date must use YYYY-MM-DD")
    if BOARDING_STOPS.get(direction) != stop:
        raise ValueError("direction and boarding stop must match")

    scheduled_time = parse_arrival(scheduled)
    actual_time = parse_arrival(actual)
    destination_time = parse_arrival(destination)

    expected_period = ""
    if scheduled:
        hour = int(scheduled[:2])
        if hour < 12:
            expected_period = "morning"
        elif hour < 17:
            expected_period = "afternoon"
        else:
            expected_period = "evening"
    if period != expected_period:
        raise ValueError("time_of_day must match the scheduled arrival")

    wait_minutes = None
    if wait:
        wait_minutes = int(wait)
        if not 0 <= wait_minutes <= 4_294_967_295:
            raise ValueError("wait_time must fit in an unsigned INT")
    if weather not in ("", "rain", "dry"):
        raise ValueError("weather must be rain, dry, or blank")

    return (
        parsed_date, direction, stop, scheduled_time, actual_time,
        period or None, destination_time, wait_minutes, weather or None,
    )


def parse_arrival(value: str) -> timedelta | None:
    """Convert a CSV time to the same format PyMySQL uses for SQL TIME."""
    if not value:
        return None

    arrival = time.fromisoformat(value)
    if arrival.strftime("%H:%M") != value:
        raise ValueError("arrival times must use HH:MM")
    return timedelta(hours=arrival.hour, minutes=arrival.minute)


def import_trips(connection: pymysql.connections.Connection, trips: list[tuple]) -> int:
    """Insert observations that are not already stored and return the count."""
    select_trips = """
        SELECT `date`, direction, stop_name, scheduled_arrival, actual_arrival,
               time_of_day, destination_arrival, wait_time, weather
        FROM bus_trips
        FOR UPDATE
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
        # Hold the database rows until commit while checking for duplicates.
        cursor.execute(select_trips)
        stored_trips = set(cursor.fetchall())
        for trip in trips:
            if trip not in stored_trips:
                cursor.execute(insert_trip, trip)
                stored_trips.add(trip)
                inserted += 1
    return inserted


def main() -> None:
    """Read the CSV, import new trips, and report the stored total."""
    try:
        trips = read_trips(CSV_PATH)
        with connect_to_database() as connection:
            added = import_trips(connection, trips)
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM bus_trips")
                (trip_count,) = cursor.fetchone()
            connection.commit()
    except (OSError, ValueError, csv.Error, pymysql.MySQLError) as error:
        print(f"Trip import failed: {error}")
        return

    print(f"Added {added} trip(s) from {CSV_PATH.name}.")
    print(f"Trips stored in bus_tracker.bus_trips: {trip_count}")


main()
