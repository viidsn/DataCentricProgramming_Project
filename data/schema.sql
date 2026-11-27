-- Create the local database if it has not been set up yet.
CREATE DATABASE IF NOT EXISTS bus_tracker
    DEFAULT CHARACTER SET utf8mb4;

USE bus_tracker;

-- Store one row per trip. Every observation field is required.
CREATE TABLE IF NOT EXISTS bus_trips (
    -- The database assigns a new ID when a trip is inserted.
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    direction ENUM('Athboy to Dublin', 'Dublin to Athboy') NOT NULL,
    stop_name ENUM('Victorine Abbey', 'Dalymount') NOT NULL,
    -- Store clock times here. Calculate delays and ride duration during analysis.
    scheduled_arrival TIME NOT NULL,
    actual_arrival TIME NOT NULL,
    time_of_day ENUM('morning', 'afternoon', 'evening') NOT NULL,
    destination_arrival TIME NOT NULL,
    -- Waiting time is measured in whole minutes and can be zero.
    wait_time INT UNSIGNED NOT NULL,
    weather ENUM('rain', 'dry') NOT NULL
);
