"""Import recorded bus trips into the bus tracker database in XAMPP."""

import csv
import os
from datetime import date, time
from pathlib import Path

import pymysql


CSV_PATH = Path(__file__).resolve().parent / "data" / "bus_trips.csv"
COLUMNS = [
    "date", "direction", "stop_name", "scheduled_arrival", "actual_arrival",
    "time_of_day", "destination_arrival", "wait_time", "weather",
]
BOARDING_STOPS = {
    "Athboy to Dublin": "Victorine Abbey",
    "Dublin to Athboy": "Dalymount",
}


def connect_to_database() -> pymysql.connections.Connection:
    """Open a connection to the local bus tracker database."""
    return pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database="bus_tracker",
        connect_timeout=5,
    )


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

    if date.fromisoformat(trip_date).isoformat() != trip_date:
        raise ValueError("date must use YYYY-MM-DD")
    if BOARDING_STOPS.get(direction) != stop:
        raise ValueError("direction and boarding stop must match")

    for value in (scheduled, actual, destination):
        if value:
            parsed_time = time.fromisoformat(value)
            if parsed_time.strftime("%H:%M") != value:
                raise ValueError("arrival times must use HH:MM")

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
        trip_date, direction, stop, scheduled or None, actual or None,
        period or None, destination or None, wait_minutes, weather or None,
    )


def import_trips(connection: pymysql.connections.Connection, trips: list[tuple]) -> int:
    """Insert observations that are not already stored and return the count."""
    # Unlike =, MySQL's <=> treats two missing values as equal.
    query = """
        INSERT INTO bus_trips (
            `date`, direction, stop_name, scheduled_arrival, actual_arrival,
            time_of_day, destination_arrival, wait_time, weather
        )
        SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s
        WHERE NOT EXISTS (
            SELECT 1 FROM bus_trips
            WHERE `date` <=> %s
              AND direction <=> %s
              AND stop_name <=> %s
              AND scheduled_arrival <=> %s
              AND actual_arrival <=> %s
              AND time_of_day <=> %s
              AND destination_arrival <=> %s
              AND wait_time <=> %s
              AND weather <=> %s
        )
    """
    inserted = 0
    with connection.cursor() as cursor:
        for trip in trips:
            # First nine values for the insert, next nine for the duplicate check.
            values = trip + trip
            inserted += cursor.execute(query, values)
    return inserted


def main() -> int:
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
        return 1

    print(f"Added {added} trip(s) from {CSV_PATH.name}.")
    print(f"Trips stored in bus_tracker.bus_trips: {trip_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
