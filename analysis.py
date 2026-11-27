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

    # Question 1. Average all recorded waiting times.
    print("1. How many minutes do I wait for the bus on average?")
    mean = trips["wait_time"].mean()
    print(f"Average wait: {mean:.2f} minutes ({len(trips)} trips).")

    # Question 2. Divide the late count by the total to get a percentage.
    print("\n2. How often does the bus arrive later than scheduled?")
    late, on_time_or_early = punctuality_counts(trips)
    total = late + on_time_or_early
    percentage = 100 * late / total
    print(f"Late arrivals: {late}/{total} ({percentage:.2f}%).")

    # Question 3. Show the mean and the number of trips for each weather group.
    print("\n3. Does the average waiting time differ between rainy and dry weather?")
    weather_summary = wait_by_weather(trips)
    for weather, row in weather_summary.iterrows():
        average = row["average_wait_minutes"]
        count = int(row["trips"])
        print(f"  {weather}: {average:.2f} minutes ({count} trips)")

    # Question 4. Compare ride durations for periods with recorded trips.
    print("\n4. How much does my average time on the bus vary between morning, afternoon, and evening trips?")
    rides = ride_time_by_period(trips)
    has_trips = rides["trips"] > 0
    recorded_periods = rides[has_trips]
    for period, row in recorded_periods.iterrows():
        count = int(row["trips"])
        average = row["average_ride_minutes"]
        if count == 1:
            trip_word = "trip"
        else:
            trip_word = "trips"
        print(f"  {period}: {average:.2f} minutes ({count} {trip_word})")

main()
