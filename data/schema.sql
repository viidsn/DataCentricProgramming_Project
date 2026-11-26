CREATE DATABASE IF NOT EXISTS bus_tracker
    DEFAULT CHARACTER SET utf8mb4;

USE bus_tracker;

CREATE TABLE IF NOT EXISTS bus_trips (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `date` DATE NOT NULL,
    direction ENUM('Athboy to Dublin', 'Dublin to Athboy') NOT NULL,
    stop_name ENUM('Victorine Abbey', 'Dalymount') NOT NULL,
    scheduled_arrival TIME NOT NULL,
    actual_arrival TIME NOT NULL,
    time_of_day ENUM('morning', 'afternoon', 'evening') NOT NULL,
    destination_arrival TIME NOT NULL,
    wait_time INT UNSIGNED NOT NULL,
    weather ENUM('rain', 'dry') NOT NULL
);
