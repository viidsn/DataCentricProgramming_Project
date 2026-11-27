"""Plot bus trip summaries with Matplotlib."""

import matplotlib.pyplot as plt
import pandas as pd
import pymysql
from matplotlib.figure import Figure

from database import (
    connect_to_database,
    load_trips,
    punctuality_counts,
    ride_time_by_period,
    wait_by_weather,
    waiting_times_over_time,
)


def plot_wait_by_weather(summary: pd.DataFrame) -> Figure:
    """Plot the mean waiting time and sample size for each weather group."""
    labels = []
    colors = []
    weather_colors = {"dry": "#C88325", "rain": "#387EAD"}
    # Put the sample size below each bar to give context for the average.
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


def plot_waiting_times(waits: pd.Series) -> Figure:
    """Plot each trip as a point and stack trips from the same date."""
    figure, ax = plt.subplots(figsize=(8, 4), layout="constrained")
    # Use date labels so each travel day gets a column of points.
    dates = waits.index.strftime("%d/%m/%y")
    ax.scatter(dates, waits, s=55, color="#387EAD")
    # The dashed line is the overall mean across trips.
    average_wait = waits.mean()
    ax.axhline(average_wait, color="#A34C36", linestyle="--",
               label=f"Average wait: {average_wait:.2f} min")
    ax.legend()
    ax.tick_params(axis="x", labelrotation=30)
    ax.set_title(f"Route 111 waiting time by date ({len(waits)} trips)")
    ax.set_xlabel("Trip date")
    ax.set_ylabel("Wait (minutes)")
    ax.set_ylim(bottom=0)
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=0.25)
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
    # The bar height is the trip count. The label also shows its share of all trips.
    labels = [f"{count} ({count / max(total, 1):.1%})" for count in counts]
    ax.bar_label(bars, labels=labels, padding=4)
    ax.set_title(f"Route 111 punctuality ({total} trips)")
    ax.set_ylabel("Number of trips")
    ax.set_ylim(0, max(1, max(counts) * 1.2))
    return figure


def plot_ride_time_by_period(summary: pd.DataFrame) -> Figure:
    """Plot average time onboard for morning, afternoon and evening trips."""
    labels = []
    for period, count in summary["trips"].items():
        trip_word = "trip" if count == 1 else "trips"
        labels.append(f"{period.capitalize()}\n({count} {trip_word})")

    figure, ax = plt.subplots(figsize=(7, 4), layout="constrained")
    # The three periods come from the summary in morning-to-evening order.
    averages = summary["average_ride_minutes"]
    bars = ax.bar(labels, averages, color="#387EAD", width=0.6)
    ax.bar_label(bars, fmt="%.2f", padding=4)
    ax.set_title("Route 111 average time on the bus by time of day")
    ax.set_ylabel("Average ride duration (minutes)")
    ax.set_ylim(0, max(1, averages.max() * 1.2))
    return figure


def main() -> None:
    """Load trip data and show all four charts."""
    try:
        with connect_to_database() as connection:
            trips = load_trips(connection)
    except pymysql.MySQLError as error:
        print(f"Could not load trips: {error}")
        return

    summary = wait_by_weather(trips)
    plot_wait_by_weather(summary)

    waits = waiting_times_over_time(trips)
    plot_waiting_times(waits)

    late, on_time_or_early = punctuality_counts(trips)
    plot_punctuality(late, on_time_or_early)

    rides = ride_time_by_period(trips)
    plot_ride_time_by_period(rides)

    # Open the windows after all four figures have been created.
    plt.show()


main()
