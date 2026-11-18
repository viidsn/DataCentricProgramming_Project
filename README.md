# Bus Punctuality Tracker

Data Centric Programming Assignment 2026 — [Assignment Brief](PROJECT_BRIEF.md)

**Status:** Proposal. Data collection and application development are planned.

# Questions

1. **Main question:** Do the buses I take in the morning arrive later on average than the ones I take in the evening?
2. Does the average arrival delay differ between the two directions?
3. What proportion of the buses I catch arrive early, on time, or late?

# Data Dictionary

Each row will represent one bus I catch on route 111 (Athboy–Dublin), observed at the stop where I board. The dataset will contain seven columns and at least 20 real observations.

| Column | Type | Units / allowed values | How it is recorded |
|--------|------|------------------------|--------------------|
| `date` | Date | `YYYY-MM-DD` | Record the local date of the trip on the day it happens. |
| `direction` | Category | `Athboy to Dublin`, `Dublin to Athboy` | Record the direction of travel on route 111. |
| `stop_name` | Category | `Victorine Abbey`, `Dalymount` | Record `Victorine Abbey` when travelling towards Dublin for university, or `Dalymount` when travelling back towards Athboy. |
| `scheduled_arrival` | Time | Local time, `HH:MM`, 24-hour clock | Manually read and transcribe the published scheduled arrival time for that stop and service, before arrival. Do not use a live prediction. |
| `actual_arrival` | Time | Local time, `HH:MM`, 24-hour clock | Read my phone clock when the bus stops for boarding and record the time to the minute. |
| `time_of_day` | Category | `morning`, `afternoon`, `evening` | Classify the scheduled time: before 12:00 = morning; 12:00–16:59 = afternoon; 17:00–23:59 = evening. |
| `delay_minutes` | Integer | Minutes; negative, zero, or positive | Calculate actual arrival minus scheduled arrival from the recorded times. This is derived from my observation. |

Positive delay means late, zero means on time at one-minute precision, and negative delay means early. Any arrival crossing midnight will be noted in the collection diary so that the delay uses the correct dates.

The time-of-day boundaries above are the proposed rules and will be fixed before the first observation.

# Description of the project

I will track how reliably the buses I take on route 111 (Athboy–Dublin) arrive on time. I always board at Victorine Abbey when travelling towards Dublin for university and at Dalymount on the return journey towards Athboy. I will manually record the scheduled and actual arrival times at these boarding stops for each bus I catch.

I will collect at least 20 observations across my travel days during the remaining semester and aim to include both morning and evening trips. I will save them in `data/bus_trips.csv` and commit the CSV to GitHub every day I record data. Multiple trips on one day will be separate rows.

I will take a few photos of my collection process for this README, avoiding identifiable information about other passengers.

The application will use Python, MySQL, pandas, and matplotlib, with a simple command-line menu. I will run the local database service through my installed XAMPP environment. Users will be able to view trips, filter by date or direction, and compare average delays by time of day.

# Instructions for use

The local database service will be started through XAMPP before running the application. Full setup and run instructions will be added when the application is built.

# How it works:

Planned workflow:

1. Record trips manually in the CSV.
2. Load them into a MySQL database running locally through XAMPP, validating dates, times, categories, missing fields, and calculated delays. Check that each boarding stop matches the recorded direction. Flag inconsistent or unusual values for review without silently removing real delays.
3. Use SQL filtering, grouping, ordering, averages, and counts to summarise trips.
4. Analyse the records with pandas, comparing morning and evening delays overall and within each direction where enough observations exist.
5. Show labelled matplotlib charts of average delay by time of day and delays over time, alongside the number of observations in each group.

# Findings

To be completed after analysing real observations. Results will describe the buses I actually catch, rather than every service on the route. I will discuss the small sample and whether direction or boarding stop could explain an apparent morning/evening difference.

## Collection diary and photos

To be added during collection, including missed observations, measurement difficulties, and any changes to the rules.

# List of files in the project

| File | Purpose | Source |
|------|---------|--------|
| `README.md` | Proposal and future project documentation | Provided template, adapted with AI assistance |
| `PROJECT_BRIEF.md` | Assignment requirements | Provided assignment brief |

The CSV, photos, and application files will be listed when added.

# References

- [Assignment brief](PROJECT_BRIEF.md) and the README template.
- The timetable source for route 111 will be added before collection begins.

# What I am most proud of in the assignment

To be completed as the project progresses.

# What I learned

To be completed with reflections on data collection, analysis, and development.
