"""Summarise bus waiting times and punctuality using pandas."""

import pandas as pd
import pymysql

from database import connect_to_database, load_trips, punctuality_counts, wait_by_weather


def average_wait(trips: pd.DataFrame) -> float | None:
    """Return the mean of recorded waiting times in minutes."""
    waits = trips["wait_time"].dropna()
    if waits.empty:
        return None
    return float(waits.mean())


def main() -> None:
    """Load the stored trips and print answers to the three research questions."""
    try:
        with connect_to_database() as connection:
            trips = load_trips(connection)
    except pymysql.MySQLError as error:
        print(f"Could not load trips: {error}")
        return

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


main()
