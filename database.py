"""Load trips from XAMPP and calculate shared summaries."""

import os

import pandas as pd
import pymysql


def connect_to_database() -> pymysql.connections.Connection:
    """Connect to the bus_tracker database in XAMPP."""
    return pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database="bus_tracker",
        connect_timeout=5,
    )


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
    averages = groups.mean()
    counts = groups.count()
    return pd.DataFrame({"average_wait_minutes": averages, "trips": counts})


def punctuality_counts(trips: pd.DataFrame) -> tuple[int, int]:
    """Count late and on-time or early trips with known arrival times."""
    delays = arrival_delays(trips)
    late = int((delays > 0).sum())
    on_time_or_early = len(delays) - late
    return late, on_time_or_early
