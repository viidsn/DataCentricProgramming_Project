"""Plot bus trip summaries with Matplotlib."""

import matplotlib.pyplot as plt
import pandas as pd
import pymysql
from matplotlib.figure import Figure

from database import (
    connect_to_database,
    load_trips,
    punctuality_counts,
    wait_by_weather,
)


def plot_wait_by_weather(summary: pd.DataFrame) -> Figure:
    """Plot the mean waiting time and sample size for each weather group."""
    labels = []
    colors = []
    weather_colors = {"dry": "#C88325", "rain": "#387EAD"}
    for weather, count in summary["trips"].items():
        trip_word = "trip" if count == 1 else "trips"
        labels.append(f"{weather.capitalize()}\n({count} {trip_word})")
        colors.append(weather_colors[weather])

    figure, ax = plt.subplots(figsize=(6, 4), layout="constrained")
    averages = summary["average_wait_minutes"]
    bars = ax.bar(labels, averages, color=colors, width=0.6)
    ax.bar_label(bars, fmt="%.2f", padding=4)
    ax.set_title("Route 111 average bus wait by weather")
    ax.set_ylabel("Average wait (minutes)")
    ax.set_ylim(0, max(1, averages.max() * 1.2))
    return figure


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


def plot_waiting_times(waits: pd.Series) -> Figure:
    """Plot one point per trip with a recorded waiting time."""
    figure, ax = plt.subplots(figsize=(8, 4), layout="constrained")
    ax.plot(waits.index, waits, marker="o", color="#387EAD")
    ax.tick_params(axis="x", labelrotation=30)
    if waits.index.min() == waits.index.max():
        timestamp = waits.index[0]
        hour = pd.Timedelta(hours=1)
        ax.set_xlim(timestamp - hour, timestamp + hour)
    ax.set_title(f"Route 111 waiting time by trip ({len(waits)} recorded)")
    ax.set_xlabel("Trip date and time")
    ax.set_ylabel("Wait (minutes)")
    ax.set_ylim(bottom=0)
    return figure


def plot_punctuality(late: int, on_time_or_early: int) -> Figure:
    """Plot counts and percentages for the two punctuality groups."""
    total = late + on_time_or_early
    counts = [late, on_time_or_early]
    figure, ax = plt.subplots(figsize=(6, 4), layout="constrained")
    bars = ax.bar(
        ["Late", "On time or early"], counts,
        color=["#B95037", "#387EAD"], width=0.6,
    )
    labels = [f"{count} ({count / total:.1%})" for count in counts]
    ax.bar_label(bars, labels=labels, padding=4)
    ax.set_title(f"Route 111 punctuality ({total} trips)")
    ax.set_ylabel("Number of trips")
    ax.set_ylim(0, max(counts) * 1.2)
    return figure


def main() -> None:
    """Load trip data and show each chart with enough data to render."""
    try:
        with connect_to_database() as connection:
            trips = load_trips(connection)
    except pymysql.MySQLError as error:
        print(f"Could not load trips: {error}")
        return

    summary = wait_by_weather(trips)
    if summary.empty:
        print("No trips with both a wait time and weather to plot.")
    else:
        plot_wait_by_weather(summary)

    waits = waiting_times_over_time(trips)
    if waits.empty:
        print("No recorded waiting times to plot over time.")
    else:
        plot_waiting_times(waits)

    late, on_time_or_early = punctuality_counts(trips)
    total = late + on_time_or_early
    if total == 0:
        print("No trips with both arrival times to plot punctuality.")
    else:
        plot_punctuality(late, on_time_or_early)

    has_chart = not summary.empty or not waits.empty or total > 0
    if has_chart:
        plt.show()


main()
