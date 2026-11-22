"""Plot bus trip summaries with Matplotlib."""

import matplotlib.pyplot as plt
import pandas as pd
import pymysql
from matplotlib.figure import Figure

from analysis import load_trips, wait_by_weather
from main import connect_to_database


def plot_wait_by_weather(summary: pd.DataFrame) -> Figure:
    """Plot the mean waiting time and sample size for each weather group."""
    labels = [
        f"{weather.capitalize()}\n({count} {'trip' if count == 1 else 'trips'})"
        for weather, count in summary["trips"].items()
    ]
    colors = {"dry": "#C88325", "rain": "#387EAD"}

    figure, ax = plt.subplots(figsize=(6, 4), layout="constrained")
    bars = ax.bar(
        labels,
        summary["average_wait_minutes"],
        color=[colors[weather] for weather in summary.index],
        width=0.6,
    )
    ax.bar_label(bars, fmt="%.2f", padding=4)
    ax.set_title("Route 111 average bus wait by weather")
    ax.set_ylabel("Average wait (minutes)")
    ax.set_ylim(0, max(1, summary["average_wait_minutes"].max() * 1.2))
    return figure


def main() -> int:
    """Load the trip data and show the weather chart when data is available."""
    try:
        with connect_to_database() as connection:
            trips = load_trips(connection)
    except pymysql.MySQLError as error:
        print(f"Could not load trips: {error}")
        return 1

    summary = wait_by_weather(trips)
    if summary.empty:
        print("No trips with both a wait time and weather to plot.")
        return 0

    plot_wait_by_weather(summary)
    plt.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
