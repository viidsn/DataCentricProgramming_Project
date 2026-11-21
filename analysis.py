"""Summarise bus waiting times and punctuality using pandas."""

import pandas as pd
import pymysql

from main import connect_to_database


def load_trips(connection: pymysql.connections.Connection) -> pd.DataFrame:
    """Read the fields needed for analysis from the bus trips table."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT wait_time, weather, scheduled_arrival, actual_arrival
            FROM bus_trips
        """)
        columns = [column[0] for column in cursor.description]
        return pd.DataFrame.from_records(cursor.fetchall(), columns=columns)


def average_wait(trips: pd.DataFrame) -> float | None:
    """Return the mean of recorded waiting times in minutes."""
    waits = trips["wait_time"].dropna()
    return None if waits.empty else float(waits.mean())


def arrival_delays(trips: pd.DataFrame) -> pd.Series:
    """Calculate delays in minutes for trips with both arrival times."""
    arrivals = trips.dropna(subset=["scheduled_arrival", "actual_arrival"])
    # PyMySQL returns SQL TIME values as timedeltas from midnight.
    scheduled = pd.to_timedelta(arrivals["scheduled_arrival"])
    actual = pd.to_timedelta(arrivals["actual_arrival"])
    return (actual - scheduled).dt.total_seconds() / 60


def wait_by_weather(trips: pd.DataFrame) -> pd.DataFrame:
    """Return the average wait and sample size for each recorded weather group."""
    recorded = trips[trips["weather"].isin(["rain", "dry"])].dropna(
        subset=["wait_time"]
    )
    return recorded.groupby("weather")["wait_time"].agg(
        trips="count", average_wait_minutes="mean"
    )


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

    delays = arrival_delays(trips)
    if delays.empty:
        print("Late arrivals: no trips with both arrival times.")
    else:
        late = int(delays.gt(0).sum())
        percentage = 100 * late / len(delays)
        print(f"Late arrivals: {late}/{len(delays)} ({percentage:.2f}%).")

    weather_summary = wait_by_weather(trips)
    if weather_summary.empty:
        print("Wait by weather: no trips with both a wait time and weather.")
    else:
        print("Average wait by weather:")
        for weather, row in weather_summary.iterrows():
            print(f"  {weather}: {row.average_wait_minutes:.2f} minutes ({int(row.trips)} trips)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
