"""Summarise bus waiting times and punctuality using pandas."""

import pandas as pd
import pymysql

from main import connect_to_database


def load_trips(connection: pymysql.connections.Connection) -> pd.DataFrame:
    """Read the fields needed for analysis from the bus trips table."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT `date`, wait_time, weather, scheduled_arrival, actual_arrival
            FROM bus_trips
            ORDER BY id
        """)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
    return pd.DataFrame(rows, columns=columns)


def average_wait(trips: pd.DataFrame) -> float | None:
    """Return the mean of recorded waiting times in minutes."""
    waits = trips["wait_time"].dropna()
    if waits.empty:
        return None
    return float(waits.mean())


def arrival_delays(trips: pd.DataFrame) -> pd.Series:
    """Calculate delays in minutes for trips with both arrival times."""
    arrivals = trips.dropna(subset=["scheduled_arrival", "actual_arrival"])
    # PyMySQL returns SQL TIME values as timedeltas from midnight.
    scheduled = pd.to_timedelta(arrivals["scheduled_arrival"])
    actual = pd.to_timedelta(arrivals["actual_arrival"])
    difference = actual - scheduled
    return difference.dt.total_seconds() / 60


def wait_by_weather(trips: pd.DataFrame) -> pd.DataFrame:
    """Return the average wait and sample size for each recorded weather group."""
    known_weather = trips["weather"].isin(["rain", "dry"])
    recorded = trips[known_weather].dropna(subset=["wait_time"])
    groups = recorded.groupby("weather")["wait_time"]
    return groups.agg(trips="count", average_wait_minutes="mean")


def waiting_times_over_time(trips: pd.DataFrame) -> pd.Series:
    """Return recorded waits indexed by trip date and boarding time."""
    recorded = trips.dropna(subset=["wait_time"])
    actual = pd.to_timedelta(recorded["actual_arrival"])
    scheduled = pd.to_timedelta(recorded["scheduled_arrival"])
    boarding_time = actual.fillna(scheduled)
    boarding_time = boarding_time.fillna(pd.Timedelta(0))
    trip_dates = pd.to_datetime(recorded["date"])
    timestamps = trip_dates + boarding_time
    waits = recorded["wait_time"].copy()
    waits.index = timestamps
    return waits.sort_index(kind="stable")


def punctuality_counts(trips: pd.DataFrame) -> tuple[int, int]:
    """Count late and on-time or early trips with known arrival times."""
    delays = arrival_delays(trips)
    late = int((delays > 0).sum())
    on_time_or_early = len(delays) - late
    return late, on_time_or_early


def main() -> int:
    """Load the stored trips and print answers to the three research questions."""
    try:
        with connect_to_database() as connection:
            trips = load_trips(connection)
    except pymysql.MySQLError as error:
        print(f"Could not load trips: {error}")
        return 1

    mean = average_wait(trips)
    if mean is None:
        print("Average wait: no recorded waiting times.")
    else:
        recorded_count = trips["wait_time"].count()
        print(f"Average wait: {mean:.2f} minutes ({recorded_count} trips).")

    late, on_time_or_early = punctuality_counts(trips)
    total = late + on_time_or_early
    if total == 0:
        print("Late arrivals: no trips with both arrival times.")
    else:
        percentage = 100 * late / total
        print(f"Late arrivals: {late}/{total} ({percentage:.2f}%).")

    weather_summary = wait_by_weather(trips)
    if weather_summary.empty:
        print("Wait by weather: no trips with both a wait time and weather.")
    else:
        print("Average wait by weather:")
        for weather, row in weather_summary.iterrows():
            average = row["average_wait_minutes"]
            count = int(row["trips"])
            print(f"  {weather}: {average:.2f} minutes ({count} trips)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
