CREATE DATABASE IF NOT EXISTS bus_tracker
    DEFAULT CHARACTER SET utf8mb4;

USE bus_tracker;

CREATE TABLE IF NOT EXISTS bus_trips (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `date` DATE NOT NULL,
    direction ENUM('Athboy to Dublin', 'Dublin to Athboy') NOT NULL,
    stop_name ENUM('Victorine Abbey', 'Dalymount') NOT NULL,
    scheduled_arrival TIME,
    actual_arrival TIME,
    time_of_day ENUM('morning', 'afternoon', 'evening'),
    destination_arrival TIME,
    wait_time INT UNSIGNED,
    weather ENUM('rain', 'dry')
);
