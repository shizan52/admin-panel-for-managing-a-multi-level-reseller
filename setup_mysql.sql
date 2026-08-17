-- MySQL Database Setup Script for Tatkal Dashboard
-- Run this script as MySQL root user to create database and user

-- Create database
CREATE DATABASE IF NOT EXISTS tatkal_db 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- Create user (change password as needed)
CREATE USER IF NOT EXISTS 'tatkal_user'@'localhost' 
    IDENTIFIED BY 'tatkal_password_123';

-- Grant all privileges on the database
GRANT ALL PRIVILEGES ON tatkal_db.* TO 'tatkal_user'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Use the database
USE tatkal_db;

-- Verify setup
SELECT 'Database setup complete!' AS Status;
SELECT DATABASE() AS CurrentDatabase;
