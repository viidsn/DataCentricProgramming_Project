USE bus_tracker;

-- 1. How many minutes do I wait for the bus on average?
SELECT
    COUNT(*) AS trips_with_wait_time,
    ROUND(AVG(wait_time), 2) AS average_wait_minutes
FROM bus_trips
WHERE wait_time IS NOT NULL;

-- 2. How often does the bus arrive later than scheduled?
SELECT
    COUNT(*) AS trips_with_arrival_times,
    COUNT(CASE WHEN actual_arrival > scheduled_arrival THEN 1 END) AS late_trips,
    ROUND(
        100.0 * COUNT(CASE WHEN actual_arrival > scheduled_arrival THEN 1 END)
        / NULLIF(COUNT(*), 0),
        2
    ) AS late_percentage
FROM bus_trips
WHERE scheduled_arrival IS NOT NULL
  AND actual_arrival IS NOT NULL;

-- 3. Does the average waiting time differ between rain and dry weather?
SELECT
    weather,
    COUNT(*) AS trips_with_wait_time,
    ROUND(AVG(wait_time), 2) AS average_wait_minutes
FROM bus_trips
WHERE weather IN ('rain', 'dry')
  AND wait_time IS NOT NULL
GROUP BY weather
ORDER BY average_wait_minutes DESC, weather;

-- 4. How much does my average time on the bus vary between morning, afternoon, and evening trips?
SELECT
    time_of_day,
    COUNT(*) AS trips,
    ROUND(AVG(TIME_TO_SEC(destination_arrival) - TIME_TO_SEC(actual_arrival)) / 60, 2)
        AS average_ride_minutes
FROM bus_trips
GROUP BY time_of_day
ORDER BY time_of_day;
