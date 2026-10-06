-- =====================================================================
-- Bank Management System - Database Schema (Refactored)
-- =====================================================================
-- Naming convention : snake_case for all tables, columns, and functions
-- Money columns      : NUMERIC(14,2) instead of FLOAT (avoids rounding errors)
-- Passwords          : stored as bcrypt hashes. Hashing and verification
--                       happen in the Python application (bcrypt library),
--                       NOT in SQL — see get_login_credentials() below.
-- =====================================================================


-- =====================================================================
-- 1. DROP EXISTING OBJECTS (children first, then parents)
-- =====================================================================
DROP TABLE IF EXISTS transactions   CASCADE;
DROP TABLE IF EXISTS loan_payments  CASCADE;
DROP TABLE IF EXISTS loans          CASCADE;
DROP TABLE IF EXISTS accounts       CASCADE;
DROP TABLE IF EXISTS employees      CASCADE;
DROP TABLE IF EXISTS users          CASCADE;


-- =====================================================================
-- 2. TABLES
-- =====================================================================

CREATE TABLE users (
    user_id       SERIAL PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    password      TEXT NOT NULL,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    birth_date    DATE NOT NULL,
    phone_number  TEXT NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_phone_number ON users(phone_number);


CREATE TABLE employees (
    employee_id     SERIAL PRIMARY KEY,
    username        TEXT NOT NULL UNIQUE,
    password        TEXT NOT NULL,
    first_name      VARCHAR(25) NOT NULL,
    middle_initial  CHAR(1),
    last_name       VARCHAR(25) NOT NULL,
    is_admin        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE accounts (
    account_number  VARCHAR(20) PRIMARY KEY,
    balance         NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (balance >= 0),
    account_name    VARCHAR(50) NOT NULL,
    user_id         INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_accounts_user_id ON accounts(user_id);


CREATE TABLE loans (
    loan_id        SERIAL PRIMARY KEY,
    account_number VARCHAR(20) NOT NULL REFERENCES accounts(account_number) ON DELETE RESTRICT,
    amount_paid    NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (amount_paid >= 0),
    start_date     DATE NOT NULL,
    due_date       DATE NOT NULL,
    total_amount   NUMERIC(14,2) NOT NULL CHECK (total_amount >= 0),
    return_amount  NUMERIC(14,2) NOT NULL CHECK (return_amount >= 0),
    CONSTRAINT chk_loan_dates CHECK (due_date >= start_date)
);

CREATE INDEX idx_loans_account_number ON loans(account_number);


CREATE TABLE loan_payments (
    payment_id     SERIAL PRIMARY KEY,
    loan_id        INTEGER NOT NULL REFERENCES loans(loan_id) ON DELETE CASCADE,
    payment_month  DATE NOT NULL,
    payment_amount NUMERIC(14,2) NOT NULL CHECK (payment_amount > 0)
);

CREATE INDEX idx_loan_payments_loan_id ON loan_payments(loan_id);


CREATE TABLE transactions (
    transaction_id    SERIAL PRIMARY KEY,
    account_number    VARCHAR(20) NOT NULL REFERENCES accounts(account_number) ON DELETE RESTRICT,
    amount             NUMERIC(14,2) NOT NULL CHECK (amount > 0),
    transaction_type   VARCHAR(8) NOT NULL CHECK (transaction_type IN ('income', 'withdraw')),
    created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_account_number ON transactions(account_number);


-- =====================================================================
-- 3. AUTHENTICATION
-- =====================================================================
-- IMPORTANT: passwords are stored as bcrypt hashes (via the Python app,
-- using the `bcrypt` library), NOT as plain text. Because every bcrypt
-- hash of the same password looks different (random salt), the database
-- can no longer compare passwords with a plain "=" — that comparison has
-- to happen in the application, using bcrypt.checkpw(). So this function
-- only *looks up* the stored hash by username; it does not verify it.

CREATE OR REPLACE FUNCTION get_login_credentials(p_username TEXT)
RETURNS TABLE (user_id INTEGER, role TEXT, password_hash TEXT) AS $$
BEGIN
    -- Try the users table first
    SELECT u.user_id, 'User'::TEXT, u.password
    INTO user_id, role, password_hash
    FROM users u
    WHERE u.username = p_username;

    -- Fall back to employees table (Employee / Admin)
    IF user_id IS NULL THEN
        SELECT e.employee_id,
               CASE WHEN e.is_admin THEN 'Admin' ELSE 'Employee' END,
               e.password
        INTO user_id, role, password_hash
        FROM employees e
        WHERE e.username = p_username;
    END IF;

    RETURN NEXT;
    RETURN;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION create_employee(
    p_username TEXT, p_password TEXT, p_first_name VARCHAR(25),
    p_middle_initial CHAR(1), p_last_name VARCHAR(25), p_is_admin BOOLEAN
) RETURNS VOID AS $$
BEGIN
    INSERT INTO employees (username, password, first_name, middle_initial, last_name, is_admin)
    VALUES (p_username, p_password, p_first_name, p_middle_initial, p_last_name, p_is_admin);
END;
$$ LANGUAGE plpgsql;


-- =====================================================================
-- 4. USERS - CRUD
-- =====================================================================

CREATE OR REPLACE FUNCTION create_user(
    p_username TEXT, p_password TEXT, p_first_name TEXT,
    p_last_name TEXT, p_birth_date DATE, p_phone_number TEXT
) RETURNS VOID AS $$
BEGIN
    INSERT INTO users (username, password, first_name, last_name, birth_date, phone_number)
    VALUES (p_username, p_password, p_first_name, p_last_name, p_birth_date, p_phone_number);
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION update_user(
    p_user_id INTEGER, p_username TEXT, p_password TEXT
) RETURNS VOID AS $$
BEGIN
    UPDATE users
    SET username = p_username,
        password = p_password
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'User with id % not found.', p_user_id;
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION delete_user(p_user_id INTEGER)
RETURNS VOID AS $$
BEGIN
    DELETE FROM users WHERE user_id = p_user_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'User with id % not found.', p_user_id;
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION read_users()
RETURNS SETOF users AS $$
BEGIN
    RETURN QUERY SELECT * FROM users;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION search_users_by_phone_number(p_phone_number TEXT)
RETURNS SETOF users AS $$
BEGIN
    RETURN QUERY SELECT * FROM users WHERE phone_number = p_phone_number;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION filter_users_by_username(p_username TEXT)
RETURNS SETOF users AS $$
BEGIN
    RETURN QUERY SELECT * FROM users WHERE username ILIKE '%' || p_username || '%';
END;
$$ LANGUAGE plpgsql;


-- =====================================================================
-- 5. ACCOUNTS - CRUD
-- =====================================================================

CREATE OR REPLACE FUNCTION create_account(
    p_account_number VARCHAR(20), p_balance NUMERIC(14,2),
    p_account_name VARCHAR(50), p_user_id INTEGER
) RETURNS VOID AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM accounts WHERE account_number = p_account_number) THEN
        RAISE EXCEPTION 'Account with number % already exists.', p_account_number;
    END IF;

    INSERT INTO accounts (account_number, balance, account_name, user_id)
    VALUES (p_account_number, p_balance, p_account_name, p_user_id);
END;
$$ LANGUAGE plpgsql;


-- NOTE: the original version silently dropped account_name from the UPDATE,
-- even though the Python CLI collected it from the user. Fixed here.
CREATE OR REPLACE FUNCTION update_account(
    p_account_number VARCHAR(20), p_new_balance NUMERIC(14,2), p_new_account_name VARCHAR(50)
) RETURNS VOID AS $$
BEGIN
    UPDATE accounts
    SET balance = p_new_balance,
        account_name = p_new_account_name
    WHERE account_number = p_account_number;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Account with number % not found.', p_account_number;
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION delete_account(p_account_number VARCHAR(20))
RETURNS VOID AS $$
DECLARE
    v_deleted VARCHAR(20);
BEGIN
    DELETE FROM accounts
    WHERE account_number = p_account_number
    RETURNING account_number INTO v_deleted;

    IF v_deleted IS NULL THEN
        RAISE EXCEPTION 'Account with number % does not exist.', p_account_number;
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION read_accounts()
RETURNS SETOF accounts AS $$
BEGIN
    RETURN QUERY SELECT * FROM accounts;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION search_account_by_account_number(p_account_number VARCHAR(20))
RETURNS SETOF accounts AS $$
BEGIN
    RETURN QUERY SELECT * FROM accounts WHERE account_number = p_account_number;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION search_account_by_user_id(p_user_id INTEGER)
RETURNS SETOF accounts AS $$
BEGIN
    RETURN QUERY SELECT * FROM accounts WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;


-- =====================================================================
-- 6. TRANSACTIONS
-- =====================================================================
-- A transaction cannot be committed if the withdrawal amount exceeds the
-- account balance. Fixed: the original version silently did nothing for
-- 'income' transactions because the INSERT/UPDATE logic was nested only
-- inside the 'withdraw' branch of the Python CLI, not the SQL itself, but
-- we make the SQL side authoritative and defensive regardless of caller.

CREATE OR REPLACE FUNCTION make_transaction(
    p_account_number VARCHAR(20), p_amount NUMERIC(14,2), p_type VARCHAR(8)
) RETURNS VOID AS $$
DECLARE
    v_balance NUMERIC(14,2);
BEGIN
    SELECT balance INTO v_balance FROM accounts WHERE account_number = p_account_number;

    IF v_balance IS NULL THEN
        RAISE EXCEPTION 'Account does not exist. Transaction aborted.';
    END IF;

    IF p_type = 'income' THEN
        INSERT INTO transactions (account_number, amount, transaction_type)
        VALUES (p_account_number, p_amount, p_type);

        UPDATE accounts SET balance = balance + p_amount WHERE account_number = p_account_number;

    ELSIF p_type = 'withdraw' THEN
        IF v_balance < p_amount THEN
            RAISE EXCEPTION 'Insufficient balance. Transaction aborted.';
        END IF;

        INSERT INTO transactions (account_number, amount, transaction_type)
        VALUES (p_account_number, p_amount, p_type);

        UPDATE accounts SET balance = balance - p_amount WHERE account_number = p_account_number;

    ELSE
        RAISE EXCEPTION 'Unknown transaction type: %', p_type;
    END IF;
END;
$$ LANGUAGE plpgsql;


-- =====================================================================
-- 7. LOANS - CRUD
-- =====================================================================

CREATE OR REPLACE FUNCTION create_loan(
    p_account_number VARCHAR(20), p_amount_paid NUMERIC(14,2), p_start_date DATE,
    p_due_date DATE, p_total_amount NUMERIC(14,2), p_return_amount NUMERIC(14,2)
) RETURNS VOID AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM accounts WHERE account_number = p_account_number) THEN
        RAISE EXCEPTION 'Account number % not found.', p_account_number;
    END IF;

    INSERT INTO loans (account_number, amount_paid, start_date, due_date, total_amount, return_amount)
    VALUES (p_account_number, p_amount_paid, p_start_date, p_due_date, p_total_amount, p_return_amount);
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION update_loan(
    p_loan_id INTEGER, p_account_number VARCHAR(20), p_amount_paid NUMERIC(14,2),
    p_start_date DATE, p_due_date DATE, p_total_amount NUMERIC(14,2), p_return_amount NUMERIC(14,2)
) RETURNS VOID AS $$
BEGIN
    UPDATE loans
    SET account_number = p_account_number,
        amount_paid    = p_amount_paid,
        start_date     = p_start_date,
        due_date       = p_due_date,
        total_amount   = p_total_amount,
        return_amount  = p_return_amount
    WHERE loan_id = p_loan_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Loan with id % not found.', p_loan_id;
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION delete_loan(p_loan_id INTEGER)
RETURNS VOID AS $$
BEGIN
    DELETE FROM loans WHERE loan_id = p_loan_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Loan with id % not found.', p_loan_id;
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION read_loans()
RETURNS SETOF loans AS $$
BEGIN
    RETURN QUERY SELECT * FROM loans;
END;
$$ LANGUAGE plpgsql;


-- Fixed: previously referenced a non-existent table "Loans" (the real
-- table is "loan"/"loans"), so this function always raised an error.
CREATE OR REPLACE FUNCTION check_loan_approval(
    p_request_date DATE, p_account_number TEXT, p_loan_amount NUMERIC(14,2)
) RETURNS BOOLEAN AS $$
DECLARE
    v_total_income NUMERIC(14,2);
    v_return_amount NUMERIC(14,2);
    v_existing_loan_count INTEGER;
BEGIN
    SELECT COALESCE(SUM(amount), 0)
    INTO v_total_income
    FROM transactions
    WHERE transaction_type = 'income'
      AND account_number = p_account_number
      AND date_trunc('month', created_at) = date_trunc('month', p_request_date);

    IF v_total_income >= 10000000 THEN
        SELECT COUNT(*)
        INTO v_existing_loan_count
        FROM loans
        WHERE account_number = p_account_number
          AND date_trunc('month', start_date) = date_trunc('month', p_request_date);

        IF v_existing_loan_count = 0 AND p_loan_amount <= v_total_income * 2 THEN
            v_return_amount := p_loan_amount * 1.2;

            INSERT INTO loans (account_number, amount_paid, start_date, due_date, total_amount, return_amount)
            VALUES (p_account_number, 0, p_request_date, p_request_date + INTERVAL '1 year', p_loan_amount, v_return_amount);

            RETURN TRUE;
        END IF;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;


-- =====================================================================
-- 8. LOAN PAYMENTS - CRUD
-- =====================================================================

CREATE OR REPLACE FUNCTION create_loan_payment(
    p_loan_id INTEGER, p_payment_month DATE, p_payment_amount NUMERIC(14,2)
) RETURNS VOID AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM loans WHERE loan_id = p_loan_id) THEN
        RAISE EXCEPTION 'Loan id % not found.', p_loan_id;
    END IF;

    INSERT INTO loan_payments (loan_id, payment_month, payment_amount)
    VALUES (p_loan_id, p_payment_month, p_payment_amount);
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION update_loan_payment(
    p_payment_id INTEGER, p_payment_month DATE, p_payment_amount NUMERIC(14,2)
) RETURNS VOID AS $$
BEGIN
    UPDATE loan_payments
    SET payment_month = p_payment_month,
        payment_amount = p_payment_amount
    WHERE payment_id = p_payment_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Loan payment id % not found.', p_payment_id;
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION delete_loan_payment(p_payment_id INTEGER)
RETURNS VOID AS $$
BEGIN
    DELETE FROM loan_payments WHERE payment_id = p_payment_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Loan payment id % not found.', p_payment_id;
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION read_loan_payments()
RETURNS SETOF loan_payments AS $$
BEGIN
    RETURN QUERY SELECT * FROM loan_payments;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION sort_loan_payments_by_date()
RETURNS SETOF loan_payments AS $$
BEGIN
    RETURN QUERY SELECT * FROM loan_payments ORDER BY payment_month;
END;
$$ LANGUAGE plpgsql;


-- Fixed: previously inserted into a non-existent table "PaymentLoan"
-- (the real table is "loan_payments"), so this procedure always failed.
CREATE OR REPLACE PROCEDURE make_loan_payment(p_loan_id INTEGER, p_payment_amount NUMERIC(14,2))
LANGUAGE plpgsql AS $$
DECLARE
    v_total_amount NUMERIC(14,2);
    v_amount_paid  NUMERIC(14,2);
    v_remaining    NUMERIC(14,2);
BEGIN
    SELECT total_amount, amount_paid
    INTO v_total_amount, v_amount_paid
    FROM loans
    WHERE loan_id = p_loan_id;

    IF v_total_amount IS NULL THEN
        RAISE EXCEPTION 'Loan id % not found.', p_loan_id;
    END IF;

    v_remaining := v_total_amount - v_amount_paid;

    IF v_remaining <= 0 THEN
        RAISE EXCEPTION 'Loan already fully paid.';
    END IF;

    IF p_payment_amount > v_remaining THEN
        RAISE EXCEPTION 'Payment amount exceeds the remaining balance.';
    END IF;

    UPDATE loans SET amount_paid = amount_paid + p_payment_amount WHERE loan_id = p_loan_id;

    INSERT INTO loan_payments (loan_id, payment_month, payment_amount)
    VALUES (p_loan_id, CURRENT_DATE, p_payment_amount);

    COMMIT;
END;
$$;


-- =====================================================================
-- 9. SAMPLE SEED DATA
-- =====================================================================

-- Passwords below are bcrypt hashes, NOT plain text.
--   john_doe / password123
--   admin    / admin123
--   emp      / 123
-- (generated with: bcrypt.hashpw(password.encode(), bcrypt.gensalt()))

INSERT INTO users (username, password, first_name, last_name, birth_date, phone_number)
VALUES ('john_doe', '$2b$12$LJn3tQ/g3UngPcilKvsGLemAuJGA9YHbLZcqIhCiO3yLk2wZqRuie', 'John', 'Doe', '1990-05-15', '+1234567890');

INSERT INTO employees (username, password, first_name, middle_initial, last_name, is_admin)
VALUES
    ('admin', '$2b$12$BHUQFES4nAHj9Wdr3O2jruNfxKI3BBj2HQqG.dBQrf9loHuDpl5SO', 'Admin', NULL, 'User', TRUE),
    ('emp',   '$2b$12$HB15CxXeXCGTl2CAX1rWxesw5CyOby8BOTt7jt0qgzjlqfW8HzkkG', 'Admin', NULL, 'User', FALSE);

INSERT INTO accounts (account_number, balance, account_name, user_id)
VALUES
    ('A001', 1000.00, 'Savings',  1),
    ('A002', 500.00,  'Checking', 1);

INSERT INTO loans (account_number, amount_paid, start_date, due_date, total_amount, return_amount)
VALUES
    ('A001', 500.00, '2021-01-01', '2022-01-01', 1000.00, 1200.00),
    ('A002', 800.00, '2021-02-01', '2023-02-01', 2000.00, 2400.00);

INSERT INTO loan_payments (loan_id, payment_month, payment_amount)
VALUES
    (1, '2021-02-01', 200.00),
    (1, '2021-03-01', 150.00),
    (2, '2021-03-01', 400.00);

INSERT INTO transactions (account_number, amount, transaction_type)
VALUES
    ('A001', 100.00, 'income'),
    ('A001', 50.00,  'withdraw');
