CREATE DATABASE IF NOT EXISTS bank_db;
USE bank_db;

-- ---------------------------------------------------------
-- 1. TEARDOWN (Drop existing tables in reverse order)
-- ---------------------------------------------------------
DROP TABLE IF EXISTS card_transactions;
DROP TABLE IF EXISTS credit_cards;
DROP TABLE IF EXISTS loan_payments;
DROP TABLE IF EXISTS loans;
DROP TABLE IF EXISTS loan_type;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS bank_branch;
DROP TABLE IF EXISTS customer;

-- ---------------------------------------------------------
-- 2. BUILD CORE ENTITIES
-- ---------------------------------------------------------
CREATE TABLE customer (
    cust_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone_num VARCHAR(15),
    address TEXT,
    dob DATE
);

CREATE TABLE accounts (
    acc_num INT AUTO_INCREMENT PRIMARY KEY,
    cust_id INT,
    pin VARCHAR(4) NOT NULL DEFAULT '0000',
    balance DECIMAL(15, 2) DEFAULT 0.00,
    open_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(10) DEFAULT 'Active',
    FOREIGN KEY (cust_id) REFERENCES customer(cust_id)
);

CREATE TABLE transactions (
    trans_id INT AUTO_INCREMENT PRIMARY KEY,
    acc_num INT,
    trans_type VARCHAR(20), 
    amount DECIMAL(15, 2),
    balance_after DECIMAL(15, 2),
    trans_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    FOREIGN KEY (acc_num) REFERENCES accounts(acc_num)
);

-- ---------------------------------------------------------
-- 3. BUILD LOAN SYSTEM
-- ---------------------------------------------------------
CREATE TABLE loan_type (
    loan_type_id INT AUTO_INCREMENT PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL,
    default_rate DECIMAL(5, 2)
);

CREATE TABLE loans (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    cust_id INT,
    loan_type_id INT,
    amount DECIMAL(15, 2) NOT NULL,
    rate DECIMAL(5, 2),
    term_months INT,
    start_date DATE,
    status VARCHAR(20) DEFAULT 'Pending',
    FOREIGN KEY (cust_id) REFERENCES customer(cust_id),
    FOREIGN KEY (loan_type_id) REFERENCES loan_type(loan_type_id)
);

CREATE TABLE loan_payments (
    pay_id INT AUTO_INCREMENT PRIMARY KEY,
    loan_id INT,
    amount DECIMAL(15, 2),
    principal_amt DECIMAL(15, 2),
    interest_amt DECIMAL(15, 2),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
);

-- ---------------------------------------------------------
-- 4. BUILD CREDIT CARD SYSTEM
-- ---------------------------------------------------------
CREATE TABLE credit_cards (
    card_num VARCHAR(16) PRIMARY KEY,
    cust_id INT,
    card_type VARCHAR(20),
    credit_limit DECIMAL(15, 2),
    expiry_date DATE,
    cvv VARCHAR(3),
    status VARCHAR(15) DEFAULT 'Active',
    FOREIGN KEY (cust_id) REFERENCES customer(cust_id)
);

CREATE TABLE card_transactions (
    card_trans_id INT AUTO_INCREMENT PRIMARY KEY,
    card_num VARCHAR(16),
    amount DECIMAL(15, 2),
    vendor_name VARCHAR(100),
    trans_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_num) REFERENCES credit_cards(card_num)
);

-- ---------------------------------------------------------
-- 5. BUILD BRANCH & EMPLOYEE SYSTEM
-- ---------------------------------------------------------
CREATE TABLE bank_branch (
    branch_id INT AUTO_INCREMENT PRIMARY KEY,
    branch_name VARCHAR(100),
    branch_address TEXT,
    city VARCHAR(50),
    state VARCHAR(50),
    branch_ifsc VARCHAR(11) UNIQUE,
    branch_contact VARCHAR(15)
);

CREATE TABLE employees (
    emp_id INT AUTO_INCREMENT PRIMARY KEY,
    branch_id INT,
    name VARCHAR(100),
    position VARCHAR(50),
    salary DECIMAL(12, 2),
    password VARCHAR(255) DEFAULT 'password123', -- Integrated directly here
    manager_id INT,
    doj DATE,
    FOREIGN KEY (branch_id) REFERENCES bank_branch(branch_id),
    FOREIGN KEY (manager_id) REFERENCES employees(emp_id)
);

-- ---------------------------------------------------------
-- 6. INSERT DEFAULT SEED DATA
-- ---------------------------------------------------------
-- A. Default Branch
INSERT INTO bank_branch (branch_name, branch_ifsc, city) 
VALUES ('Main Jaipur Branch', 'BANK0001234', 'Jaipur');

-- B. Default Admin
INSERT INTO employees (branch_id, name, position, salary, password, doj) 
VALUES (1, 'Admin User', 'Manager', 75000.00, 'admin_pass', CURDATE());

-- C. Loan Offerings
INSERT INTO loan_type (type_name, default_rate) VALUES 
('Personal Loan', 10.50),
('Home Loan', 7.25),
('Education Loan', 8.00),
('Car Loan', 9.50);

SELECT * FROM employees;
-- 1. Check if the Loan status actually changed from 'Pending' to 'Approved'
SELECT * FROM loans;

-- 2. Check if the credit card swipe was recorded
SELECT * FROM card_transactions;

-- 3. Verify the Bank's total liquidity matches Alice's 10,000 balance
SELECT SUM(balance) FROM accounts;