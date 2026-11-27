"""Import recorded bus trips into the XAMPP database."""

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

import pymysql

from database import connect_to_database, load_trip_table


CSV_PATH = Path(__file__).resolve().parent / "data" / "bus_trips.csv"
COLUMNS = [
    "date",
    "direction",
    "stop_name",
    "scheduled_arrival",
    "actual_arrival",
    "time_of_day",
    "destination_arrival",
    "wait_time",
    "weather",
]
BOARDING_STOPS = {
    "Athboy to Dublin": "Victorine Abbey",
    "Dublin to Athboy": "Dalymount",
}


def read_trips(path: Path) -> list[tuple] | None:
    """Read and validate complete trip observations from the CSV."""
    trips = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            # fieldnames comes from the header. The loop below checks the trip rows.
            if reader.fieldnames != COLUMNS:
                raise ValueError("The CSV headers do not match the trip columns.")

            for row in reader:
                trips.append(parse_trip(row))
    except (OSError, csv.Error) as error:
        print(f"Could not read CSV: {error}")
        return None
    return trips


def parse_trip(row: dict[str, str | None]) -> tuple:
    """Check a CSV row against the measurement rules in the README."""
    # DictReader puts extra values under an extra key and fills missing values with None.
    if len(row) != len(COLUMNS):
        raise ValueError("The trip has extra fields")
    # Check all values for anomalies
    fields = {}
    for column in COLUMNS:
        value = row[column]
        if value is None:
            raise ValueError("All trip fields are required")
        value = value.strip()
        if value == "":
            raise ValueError("All trip fields are required")
        fields[column] = value

    trip_date = fields["date"]
    direction = fields["direction"]
    stop = fields["stop_name"]
    scheduled = fields["scheduled_arrival"]
    actual = fields["actual_arrival"]
    period = fields["time_of_day"]
    destination = fields["destination_arrival"]
    wait = fields["wait_time"]
    weather = fields["weather"]

    # Check the date according to the rules in README
    parsed_date = date.fromisoformat(trip_date)
    if parsed_date.isoformat() != trip_date:
        raise ValueError("date must use YYYY-MM-DD")
    # Check the direction and stop according to the rules in README
    if BOARDING_STOPS.get(direction) != stop:
        raise ValueError("direction and boarding stop must match")

    scheduled_time = parse_arrival(scheduled)
    actual_time = parse_arrival(actual)
    destination_time = parse_arrival(destination)

    # Check the period according to the rules in README
    # Use the scheduled hour so a delay cannot move a trip to a different period.
    hour = int(scheduled[:2])
    if hour < 12:
        expected_period = "morning"
    elif hour < 17:
        expected_period = "afternoon"
    else:
        expected_period = "evening"
    if period != expected_period:
        raise ValueError("time_of_day must match the scheduled arrival")

    # Check the wait_time to see if the number is real
    wait_minutes = int(wait)
    if not 0 <= wait_minutes <= 4_294_967_295:
        raise ValueError("wait_time must fit in an unsigned INT")

    # Check the weather according to the rules in README
    if weather not in ("rain", "dry"):
        raise ValueError("weather must be rain or dry")

    # Keep this tuple in the same order as the columns in the INSERT below.
    return (
        parsed_date,
        direction,
        stop,
        scheduled_time,
        actual_time,
        period,
        destination_time,
        wait_minutes,
        weather,
    )


def parse_arrival(value: str) -> timedelta:
    """Convert a CSV time to the same format PyMySQL uses for SQL TIME."""
    if len(value) != 5 or not value.isascii():
        raise ValueError("arrival times must use HH:MM")
    arrival = datetime.strptime(value, "%H:%M")
    # PyMySQL reads SQL TIME as a timedelta, so both sources can be compared directly.
    return timedelta(hours=arrival.hour, minutes=arrival.minute)


def import_trips(connection: pymysql.connections.Connection, trips: list[tuple]) -> None:
    """Insert observations that are not already stored and return the count."""
    select_trips = """
        SELECT date, direction, stop_name, scheduled_arrival, actual_arrival,
               time_of_day, destination_arrival, wait_time, weather
        FROM bus_trips
    """
    # PyMySQL replaces each %s with the matching value from the trip tuple.
    insert_trip = """
        INSERT INTO bus_trips (
            date, direction, stop_name, scheduled_arrival, actual_arrival,
            time_of_day, destination_arrival, wait_time, weather
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    inserted = 0
    with connection.cursor() as cursor:
        cursor.execute(select_trips)
        # Check all nine values to find an exact duplicate.
        stored_trips = list(cursor.fetchall())
        for trip in trips:
            if trip not in stored_trips:
                cursor.execute(insert_trip, trip)
                # Also skip repeated rows within this CSV import.
                stored_trips.append(trip)
                inserted += 1

        print(f"Added {inserted} trip(s) from {CSV_PATH.name}.")
    return


def main() -> None:
    """Run the bus tracker menu."""
    while True:
        print("\n=== Bus Punctuality Tracker ===")
        print("1. Import trips from CSV")
        print("2. Show all trips")
        print("3. Filter trips by date")
        print("4. Filter trips by weather")
        print("5. Show summary")
        print("6. Show charts")
        print("0. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            try:
                # Validate the whole file before opening the database connection.
                trips = read_trips(CSV_PATH)
                if trips is None:
                    continue
                with connect_to_database() as connection:
                    import_trips(connection, trips)
                    # Save the insertions together once the import finishes.
                    connection.commit()
            except ValueError as error:
                print(f"Trip import failed: {error}")
                continue
            except pymysql.MySQLError as error:
                print(f"Database error: {error}")
        elif choice == "2":
            try:
                with connect_to_database() as connection:
                    table = load_trip_table(connection)
                print(table.to_string(index=False))
            except pymysql.MySQLError as error:
                print(f"Could not load trips: {error}")
        elif choice == "3":
            try:
                selected_date = date.fromisoformat(input("Enter date (YYYY-MM-DD): ").strip())
                with connect_to_database() as connection:
                    table = load_trip_table(connection)
                # Creating pandas Series to compare the DataFrame with the filter
                matches = table["date"] == selected_date
                matching_trips = table[matches]
                if matching_trips.empty:
                    print(f"No trips found for {selected_date}.")
                else:
                    print(matching_trips.to_string(index=False))
            except ValueError:
                print("Enter a valid date in YYYY-MM-DD format.")
            except pymysql.MySQLError as error:
                print(f"Could not load trips: {error}")
        elif choice == "0":
            break


main()
