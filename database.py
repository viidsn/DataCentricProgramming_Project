"""Load trips from XAMPP and calculate shared summaries."""

import pandas as pd
import pymysql


def connect_to_database() -> pymysql.connections.Connection:
    """Connect to the bus_tracker database in XAMPP."""
    return pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="",
        database="bus_tracker",
        connect_timeout=5,
    )


def load_trips(connection: pymysql.connections.Connection) -> pd.DataFrame:
    """Read the fields needed for analysis from the bus trips table."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT `date`, wait_time, weather, scheduled_arrival, actual_arrival,
                   destination_arrival, time_of_day
            FROM bus_trips
            ORDER BY id
        """)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
    return pd.DataFrame(rows, columns=columns)


def arrival_delays(trips: pd.DataFrame) -> pd.Series:
    """Calculate the difference between actual and scheduled arrival in minutes."""
    # PyMySQL returns SQL TIME values as timedeltas from midnight.
    scheduled = pd.to_timedelta(trips["scheduled_arrival"])
    actual = pd.to_timedelta(trips["actual_arrival"])
    difference = actual - scheduled
    return difference.dt.total_seconds() / 60


def wait_by_weather(trips: pd.DataFrame) -> pd.DataFrame:
    """Return the average wait and sample size for each recorded weather group."""
    groups = trips.groupby("weather")["wait_time"]
    averages = groups.mean()
    counts = groups.count()
    return pd.DataFrame({"average_wait_minutes": averages, "trips": counts})


def waiting_times_over_time(trips: pd.DataFrame) -> pd.Series:
    """Return one waiting time per trip, sorted by date."""
    waits = trips["wait_time"].copy()
    waits.index = pd.to_datetime(trips["date"])
    return waits.sort_index(kind="stable")


def punctuality_counts(trips: pd.DataFrame) -> tuple[int, int]:
    """Count late trips and trips that arrived on time or early."""
    delays = arrival_delays(trips)
    late = int((delays > 0).sum())
    on_time_or_early = len(delays) - late
    return late, on_time_or_early


def ride_time_by_period(trips: pd.DataFrame) -> pd.DataFrame:
    """Return average onboard minutes and trip count for each time of day."""
    periods = ["morning", "afternoon", "evening"]
    rides = trips.copy()

    boarding_time = pd.to_timedelta(rides["actual_arrival"])
    destination_time = pd.to_timedelta(rides["destination_arrival"])
    duration = destination_time - boarding_time
    # A destination time earlier than boarding is treated as the next day.
    after_midnight = duration < pd.Timedelta(0)
    duration.loc[after_midnight] += pd.Timedelta(days=1)
    rides["ride_minutes"] = duration.dt.total_seconds() / 60

    groups = rides.groupby("time_of_day")["ride_minutes"]
    averages = groups.mean().reindex(periods)
    counts = groups.count().reindex(periods, fill_value=0)
    return pd.DataFrame({"average_ride_minutes": averages, "trips": counts})
