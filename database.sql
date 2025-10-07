DROP DATABASE IF EXISTS college;
CREATE DATABASE college;
USE college;

-- student table
CREATE TABLE student_details (
    id_num VARCHAR(7) NOT NULL PRIMARY KEY,
    name VARCHAR(20),
    email VARCHAR(20),
    phone VARCHAR(10),
    password VARCHAR(8)
);

-- faculty table
DROP TABLE IF EXISTS faculty;
CREATE TABLE faculty (
    id_num VARCHAR(10) NOT NULL PRIMARY KEY,
    name VARCHAR(20),
    email VARCHAR(20),
    phone VARCHAR(10),
    password VARCHAR(8),
    hod VARCHAR(1) DEFAULT 'n'
);

-- leave application table
DROP TABLE IF EXISTS leave_application;
CREATE TABLE leave_application (
    num INT AUTO_INCREMENT PRIMARY KEY,
    id_num VARCHAR(7),
    from_date VARCHAR(15),
    to_date VARCHAR(15),
    reason VARCHAR(200),
    status VARCHAR(1) DEFAULT 'c'
);

-- comments table
DROP TABLE IF EXISTS comments;
CREATE TABLE comments (
    num INT,
    comment VARCHAR(25)
);

-- Optional: Create user (skip if already done)
-- CREATE USER IF NOT EXISTS 'monkey'@'localhost' IDENTIFIED BY '30012003@jan';
-- GRANT ALL PRIVILEGES ON college.* TO 'monkey'@'localhost';

-- Sample faculty records
INSERT INTO faculty (id_num, name, email, phone, password, hod) VALUES
('f1', 'f1', 'f1@gmail.com', 'f1', 'f1', 'n'),
('f2', 'f2', 'f2@gmail.com', 'f2', 'f2', 'n'),
('h1', 'h1', 'h1@gmail.com', 'h1', 'h1', 'y');
