"""Import recorded bus trips into the bus tracker database in XAMPP."""

import csv
import os
from datetime import date, time
from pathlib import Path

import pymysql


CSV_PATH = Path(__file__).resolve().parent / "data" / "bus_trips.csv"
COLUMNS = (
    "date", "direction", "stop_name", "scheduled_arrival", "actual_arrival",
    "time_of_day", "destination_arrival", "wait_time", "weather",
)
BOARDING_STOPS = {
    "Athboy to Dublin": "Victorine Abbey",
    "Dublin to Athboy": "Dalymount",
}


def read_trips(path: Path) -> list[tuple]:
    """Read and validate observations, converting blank fields to None."""
    trips = []
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source, strict=True)
        if next(reader, None) != list(COLUMNS):
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
    trip_date, direction, stop, scheduled, actual, period, destination, wait, weather = (
        field.strip() for field in row
    )

    if date.fromisoformat(trip_date).isoformat() != trip_date:
        raise ValueError("date must use YYYY-MM-DD")
    if direction not in BOARDING_STOPS or BOARDING_STOPS[direction] != stop:
        raise ValueError("direction and boarding stop must match")

    for value in (scheduled, actual, destination):
        if value and time.fromisoformat(value).isoformat(timespec="minutes") != value:
            raise ValueError("arrival times must use HH:MM")

    expected_period = ""
    if scheduled:
        hour = time.fromisoformat(scheduled).hour
        if hour < 12:
            expected_period = "morning"
        elif hour < 17:
            expected_period = "afternoon"
        else:
            expected_period = "evening"
    if period != expected_period:
        raise ValueError("time_of_day must match the scheduled arrival")

    wait_minutes = int(wait) if wait else None
    if wait_minutes is not None and not 0 <= wait_minutes <= 4_294_967_295:
        raise ValueError("wait_time must fit in an unsigned INT")
    if weather not in ("", "rain", "dry"):
        raise ValueError("weather must be rain, dry, or blank")

    return (
        trip_date, direction, stop, scheduled or None, actual or None,
        period or None, destination or None, wait_minutes, weather or None,
    )


def import_trips(connection, trips: list[tuple]) -> int:
    """Insert observations that are not already stored and return the count."""
    columns = ", ".join(f"`{column}`" for column in COLUMNS)
    placeholders = ", ".join(["%s"] * len(COLUMNS))
    # MySQL's <=> operator considers two NULL values equal.
    matches = " AND ".join(f"`{column}` <=> %s" for column in COLUMNS)
    query = f"""
        INSERT INTO bus_trips ({columns})
        SELECT {placeholders}
        WHERE NOT EXISTS (SELECT 1 FROM bus_trips WHERE {matches})
    """
    inserted = 0
    with connection.cursor() as cursor:
        for trip in trips:
            inserted += cursor.execute(query, trip + trip)
    return inserted


def main() -> int:
    """Read the CSV, import new trips, and report the stored total."""
    try:
        trips = read_trips(CSV_PATH)
        with pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database="bus_tracker",
            connect_timeout=5,
        ) as connection:
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
