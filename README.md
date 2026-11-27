# Bus Punctuality Tracker

Data Centric Programming Assignment 2026 — [Assignment Brief](PROJECT_BRIEF.md)

**Status:** Data collection is ongoing. CSV import, SQL queries, the pandas report, and four charts are ready. The interactive menu is planned.

# Questions

1. How many minutes do I wait for the bus on average?
2. How often does the bus arrive later than scheduled?
3. Does the average waiting time differ between rainy and dry weather?
4. How much does my average time on the bus vary between morning, afternoon, and evening trips?

# Data Dictionary

Each row describes one trip I take on route 111 (Athboy–Dublin). I record observations at my boarding stop and at my destination. The dataset will contain nine columns and at least 20 real observations.

| Column | Type | Units / allowed values | How it is recorded |
|--------|------|------------------------|--------------------|
| `date` | Date | `YYYY-MM-DD` | Record the local date of the trip on the day it happens. |
| `direction` | Category | `Athboy to Dublin`, `Dublin to Athboy` | Record the direction of travel on route 111. |
| `stop_name` | Category | `Victorine Abbey`, `Dalymount` | Record `Victorine Abbey` when travelling towards Dublin for university, or `Dalymount` when travelling back towards Athboy. |
| `scheduled_arrival` | Time | Local time, `HH:MM`, 24-hour clock | Before the bus arrives, write down the published arrival time for that stop and service. Do not use a live prediction. |
| `actual_arrival` | Time | Local time, `HH:MM`, 24-hour clock | Read my phone clock when the bus stops for boarding and record the time to the minute. |
| `time_of_day` | Category | `morning`, `afternoon`, `evening` | Classify the scheduled time: before 12:00 = morning; 12:00–16:59 = afternoon; 17:00–23:59 = evening. |
| `destination_arrival` | Time | Local time, `HH:MM`, 24-hour clock | Read my phone clock when the bus reaches the destination stop where I get off and record the time to the minute. |
| `wait_time` | Integer | Minutes, zero or greater | Measure the elapsed time from when I reach the boarding stop until the bus stops for boarding, using my phone clock or stopwatch, and record it to the nearest minute. |
| `weather` | Category | `rain`, `dry` | Record `rain` if it rains at any point during the wait. Otherwise record `dry`. |

`delay_minutes` is calculated during analysis by subtracting the scheduled arrival time from the actual arrival time. The CSV stores the two arrival times. A positive delay means late, zero means on time to the nearest minute, and a negative delay means early. Waiting time starts when I reach the stop, regardless of the timetable. The delay calculation assumes both arrival times fall on the same calendar day. I will note any exceptions in the collection diary.

All nine fields are required for every trip. If any field is blank, the import stops before saving trips. A waiting time of zero minutes is valid.

The same time-of-day boundaries apply to every observation.

# Description of the project

I will track how long I wait and how reliably the buses I take on route 111 (Athboy–Dublin) arrive on time. I always board at Victorine Abbey when travelling towards Dublin for university and at Dalymount on the return journey towards Athboy. I will manually record the scheduled and actual arrival times at these boarding stops, my waiting time, the weather during the wait, and the time the bus reaches the destination stop where I get off.

I will collect at least 20 observations across my travel days during the remaining semester and aim to include both morning and evening trips. I will save them in `data/bus_trips.csv` and commit the CSV to GitHub every day I record data. Multiple trips on one day will be separate rows.

I will take a few photos of my collection process for this README, avoiding identifiable information about other passengers.

The application will use Python, MySQL, pandas, and matplotlib, with a simple command-line menu. I will run the local database service through my installed XAMPP environment. Users will be able to view trips, filter by date or direction, see average waiting time and the proportion of late buses, and compare average waiting times in rain and dry weather.

# Instructions for use

Start **MySQL Database** in XAMPP. Set up the project's virtual environment from the project directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Import [data/schema.sql](data/schema.sql) in phpMyAdmin to create the `bus_tracker` database and its `bus_trips` table. Then run `.venv/bin/python main.py` to import the observations from `data/bus_trips.csv`.

The script checks the entire CSV before inserting any trips. If a row is invalid, the import stops. It skips any row whose nine values match a stored trip, then reports how many trips it added. If you correct a row already in the database, the script inserts the corrected row as a new trip.

The script connects to `127.0.0.1:3306` using the local XAMPP `root` account with an empty password. The connection settings are in `database.py`.

## SQL queries

After importing the trips, open the SQL tab in phpMyAdmin and run [data/queries.sql](data/queries.sql). The queries report the overall average wait, the count and percentage of late buses, the average wait by weather, and the average ride duration by time of day.

The late-arrival query compares times within the same calendar day. A trip whose scheduled and actual arrival fall on opposite sides of midnight needs a date-aware comparison.

## Python analysis

After importing the CSV, run `.venv/bin/python analysis.py`. The report uses pandas to calculate the average wait, the share of buses that arrived late, and the average wait and trip count for each weather category. As with the SQL queries, the delay calculation assumes both arrival times fall on the same calendar day.

The report also compares average time on the bus for morning, afternoon, and evening trips. Ride duration is `destination_arrival` minus `actual_arrival` in minutes, with both times on the same calendar day. The comparison uses the scheduled `time_of_day` of each trip.

Run `.venv/bin/python charts.py` to open four charts showing average wait by weather, waiting time by trip, arrival punctuality, and average ride duration by time of day. The waiting-time scatter plot shows one point per trip and groups trips from the same date in a column. A dashed line shows the average across all trips. After adding observations, import the CSV again with `.venv/bin/python main.py` so the new trips appear in the charts.

# How it works:

Current workflow:

1. Record trips manually in the CSV.
2. Load them into a MySQL database running locally through XAMPP, validating dates, times, categories, missing fields, and non-negative waiting times. Check that each boarding stop matches the recorded direction. Flag inconsistent or unusual values for review without silently removing real observations.
3. Use SQL filtering, grouping, ordering, averages, and counts to summarise trips.
4. Use pandas to calculate arrival delays, average waiting time, and the count and percentage of late buses. Compare average waiting times in `rain` and `dry` weather and average ride durations across the three times of day.
5. Show labelled matplotlib charts for waiting times over time, average wait by weather, punctuality, and average ride duration by time of day. Include sample counts for each summary.

# Findings

To be completed after analysing real observations. Results will describe the buses I actually catch, rather than every service on the route. I will discuss the small sample, unequal weather-group sizes, and how my arrival time at the stop, direction, or time of day could affect waiting-time comparisons. A weather association alone will not establish that rain causes longer waits.

## Collection diary and photos

- **2026-11-19:** First observation: the bus was scheduled to arrive at Victorine Abbey towards Dublin at 13:08 and actually arrived at 13:10. I waited 11 minutes in rain and reached my destination at 14:01. This is an afternoon trip. Added `destination_arrival`, `wait_time`, and `weather`; arrival delays will be calculated during analysis rather than stored in the CSV.

I photographed the posted timetables at both boarding stops. I use these signs to look up the scheduled times for route 111.

![Posted timetable at Victorine Abbey](docs/images/victorine-abbey.jpg)

*Victorine Abbey — route 111 towards Dublin (Busáras).*

![Posted timetable at Dalymount](docs/images/dalymont.jpg)

*Dalymount — route 111 towards Athboy.*

![Phone notes with four bus trips recorded on 19 and 20 November 2026](docs/images/data%20collection.jpg)

*My manual trip notes. Each line shows when I reached the stop, when the bus arrived, and when I reached my destination.*

# List of files in the project

| File | Purpose | Source |
|------|---------|--------|
| `README.md` | Proposal and future project documentation | Based on the provided template |
| `PROJECT_BRIEF.md` | Assignment requirements | Provided assignment brief |
| `data/bus_trips.csv` | CSV headers and manually recorded bus observations | Own observations |
| `data/schema.sql` | SQL script to create the database and trips table | Project database schema |
| `data/queries.sql` | SQL summaries for all four research questions | Project analysis queries |
| `main.py` | Imports trip observations from CSV | Project application code |
| `database.py` | Connects to XAMPP, loads trips and calculates shared summaries for the report and charts | Project database and analysis code |
| `analysis.py` | Text summaries of waiting times, punctuality, waiting times by weather, and ride duration by time of day | Project analysis code |
| `charts.py` | Matplotlib charts of waiting times, waiting times by weather, punctuality, and ride duration by time of day | Project chart code |
| `data/route_111_timetable.txt` | Timetable reference for both boarding stops | Transcribed from the posted timetables |
| `docs/images/` | Photos of the posted timetables and a screenshot of my trip notes | Own photos and notes |

# References

- [Assignment brief](PROJECT_BRIEF.md) and the README template.
- Bus Éireann route 111 timetables posted at Victorine Abbey and Dalymount. See the [transcribed timetable](data/route_111_timetable.txt).

# What I am most proud of in the assignment

To be completed as the project progresses.

# What I learned

To be completed with reflections on data collection, analysis, and development.
