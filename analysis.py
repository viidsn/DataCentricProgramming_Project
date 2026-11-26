"""Summarise bus waiting times, punctuality and ride duration using pandas."""

import pymysql

from database import (
    connect_to_database,
    load_trips,
    punctuality_counts,
    ride_time_by_period,
    wait_by_weather,
)


def main() -> None:
    """Load the stored trips and print answers to the research questions."""
    try:
        with connect_to_database() as connection:
            trips = load_trips(connection)
    except pymysql.MySQLError as error:
        print(f"Could not load trips: {error}")
        return

    mean = trips["wait_time"].mean()
    print(f"Average wait: {mean:.2f} minutes ({len(trips)} trips).")

    late, on_time_or_early = punctuality_counts(trips)
    total = late + on_time_or_early
    percentage = 100 * late / total
    print(f"Late arrivals: {late}/{total} ({percentage:.2f}%).")

    weather_summary = wait_by_weather(trips)
    print("Average wait by weather:")
    for weather, row in weather_summary.iterrows():
        average = row["average_wait_minutes"]
        count = int(row["trips"])
        print(f"  {weather}: {average:.2f} minutes ({count} trips)")

    rides = ride_time_by_period(trips)
    recorded_periods = rides[rides["trips"] > 0]
    print("Average time on the bus by time of day:")
    for period, row in recorded_periods.iterrows():
        count = int(row["trips"])
        average = row["average_ride_minutes"]
        trip_word = "trip" if count == 1 else "trips"
        print(f"  {period}: {average:.2f} minutes ({count} {trip_word})")

main()
