-- ══════════════════════════════════════════════════════════
-- FinanceFlow — MySQL Database Schema
-- Run this FIRST in XAMPP phpMyAdmin or MySQL CLI
-- ══════════════════════════════════════════════════════════

-- Create database
CREATE DATABASE IF NOT EXISTS finance_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE finance_db;

-- ── Users Table ──
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_email (email)
) ENGINE=InnoDB;

-- ── Income Table ──
CREATE TABLE IF NOT EXISTS income (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount DOUBLE NOT NULL,
    source VARCHAR(100) NOT NULL,
    date DATE NOT NULL DEFAULT (CURRENT_DATE),
    description VARCHAR(255) DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_income_user (user_id),
    INDEX idx_income_date (date),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── Expenses Table ──
CREATE TABLE IF NOT EXISTS expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount DOUBLE NOT NULL,
    category VARCHAR(100) NOT NULL,
    date DATE NOT NULL DEFAULT (CURRENT_DATE),
    description VARCHAR(255) DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_expenses_user (user_id),
    INDEX idx_expenses_date (date),
    INDEX idx_expenses_category (category),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── Budgets Table ──
CREATE TABLE IF NOT EXISTS budgets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category VARCHAR(100) NOT NULL,
    limit_amount DOUBLE NOT NULL,
    month INT NOT NULL,
    year INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_budgets_user (user_id),
    UNIQUE KEY uq_user_cat_month_year (user_id, category, month, year),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;
