-- ============================================================
-- Real Estate Management System – MySQL setup script
-- Run this ONCE to create DB + tables + default admin user
-- Usage:  mysql -u root -p < setup_database.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS real_estate_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE real_estate_db;

-- ── users ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    username   VARCHAR(50)  UNIQUE NOT NULL,
    password   VARCHAR(255) NOT NULL,           -- bcrypt hash
    email      VARCHAR(100),
    contact    VARCHAR(20),
    role       ENUM('admin','agent') DEFAULT 'agent',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── properties ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS properties (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(200) NOT NULL,
    type        ENUM('House','Apartment','Villa','Commercial','Plot') NOT NULL,
    location    VARCHAR(200) NOT NULL,
    price       DECIMAL(15,2) NOT NULL,
    size        VARCHAR(50),
    description TEXT,
    image_paths TEXT,                            -- pipe-separated file paths
    status      ENUM('Available','Under Negotiation','Sold','Rented') DEFAULT 'Available',
    added_by    INT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (added_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ── transactions ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transactions (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT,
    client_name VARCHAR(100) NOT NULL,
    amount      DECIMAL(15,2) NOT NULL,
    type        ENUM('Sale','Rent') NOT NULL,
    date        DATE NOT NULL,
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE SET NULL
);

-- ── customers ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    contact    VARCHAR(20),
    email      VARCHAR(100),
    address    TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── appointments ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS appointments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT,
    client_name VARCHAR(100) NOT NULL,
    date        DATE NOT NULL,
    time        TIME NOT NULL,
    status      ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE SET NULL
);

-- ── favorites ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS favorites (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT,
    property_id INT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)     REFERENCES users(id)      ON DELETE CASCADE,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
    UNIQUE KEY uq_fav (user_id, property_id)
);

-- ── Seed default admin (password: admin123) ───────────────────
-- The hash below is for "admin123" via bcrypt.
-- The application also seeds this automatically if no admin exists.
INSERT IGNORE INTO users (name, username, password, email, contact, role)
VALUES (
  'Administrator',
  'admin',
  '$2b$12$GptMEb1m5k5sGKJDhTxYR.qimW5IsTGqKVvRhOT3RK4UGKQ9nRyqa',
  'admin@realestate.com',
  '0000000000',
  'admin'
);

-- ── Sample data (optional) ─────────────────────────────────────
INSERT IGNORE INTO properties (title, type, location, price, size, description, status, added_by)
VALUES
  ('Sunset Villa', 'Villa', 'Mumbai', 15000000, '3200 sqft', 'Luxury 4BHK villa with pool', 'Available', 1),
  ('City Apartment', 'Apartment', 'Pune', 4500000, '1100 sqft', 'Modern 2BHK in city centre', 'Available', 1),
  ('Commercial Space', 'Commercial', 'Delhi', 8500000, '2000 sqft', 'Ground floor commercial unit', 'Available', 1);

SELECT 'Setup complete! Default admin: username=admin  password=admin123' AS info;
