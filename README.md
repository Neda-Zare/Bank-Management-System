# 🏦 Bank Management System

A desktop **Bank Management System** built with **Python, Tkinter, and
PostgreSQL**.

The project provides a role-based banking application with a graphical
user interface for customers, employees, and administrators. It manages
users, bank accounts, transactions, loans, loan payments, and employee
accounts while keeping the database logic in PostgreSQL functions and
procedures.

------------------------------------------------------------------------

## ✨ Features

### 🔐 Authentication & Roles

The system supports three roles:

-   **User** --- bank customer
-   **Employee** --- bank staff
-   **Admin** --- employee with administrative privileges

Passwords are stored as **bcrypt hashes** rather than plain text.
Password verification is performed in the Python application.

### 👤 User Management

Employees and administrators can:

-   View all users
-   Search users by username
-   Search users by phone number
-   Create users
-   Update user information
-   Delete users

Customers can also create their own account through the registration
screen.

### 💳 Account Management

Employees and administrators can:

-   View all bank accounts
-   Search accounts
-   Search accounts by user
-   Create accounts
-   Update accounts
-   Delete accounts

When creating an account, the owner can be selected from a **user
dropdown**, so the database `user_id` does not need to be entered
manually.

### 💸 Transactions

Customers can perform banking transactions such as:

-   Deposits / income
-   Withdrawals

Transaction records are associated with the corresponding bank account.

### 🏦 Loans

Customers can:

-   Request a loan
-   Check loan approval
-   View their loans
-   Make loan payments

Employees and administrators can:

-   View loans
-   Create loans
-   Update loans
-   Delete loans
-   Manage loan payments

### 👨‍💼 Employee Management

Administrators can create employee accounts and specify whether an
employee has administrative privileges.

------------------------------------------------------------------------

## 🖥️ User Interface

The application uses a clean desktop GUI built with **Tkinter and ttk**.

The interface includes:

-   Login and registration screens
-   Role-based dashboards
-   Sidebar navigation
-   User management
-   Account management
-   Loan management
-   Loan payment management
-   Transaction forms
-   Input validation and database error handling

------------------------------------------------------------------------

## 🏗️ Project Architecture

The project separates the graphical interface from the database/business
logic:

``` text
BankProject/
│
├── gui.py              # Tkinter graphical user interface
├── bank_cli.py         # Database connection and business/database helpers
├── database.sql        # PostgreSQL schema, functions, procedures, and sample data
└── README.md
```

The GUI communicates with PostgreSQL through the existing Python
database layer, while PostgreSQL functions and procedures handle the
main database operations.

------------------------------------------------------------------------

## 🗄️ Database Design

The PostgreSQL database contains the following main tables:

``` text
users
  │
  └── accounts
        │
        ├── transactions
        │
        └── loans
              │
              └── loan_payments

employees
```

### Main tables

  Table             Description
  ----------------- -------------------------------
  `users`           Bank customers
  `employees`       Employees and administrators
  `accounts`        Customer bank accounts
  `transactions`    Income and withdrawal records
  `loans`           Customer loans
  `loan_payments`   Loan installment payments

The database also uses:

-   Primary and foreign keys
-   Unique constraints
-   Check constraints
-   Indexes
-   PostgreSQL functions
-   PostgreSQL procedures
-   Referential integrity

------------------------------------------------------------------------

## 🔒 Security

The project uses **bcrypt** for password hashing.

Passwords are not stored as plain text:

``` text
User password
      │
      ▼
   bcrypt
      │
      ▼
Password hash
      │
      ▼
 PostgreSQL
```

During login, the application retrieves the stored hash and verifies the
entered password using bcrypt.


------------------------------------------------------------------------

## 🛠️ Technologies

  Technology           Purpose
  -------------------- -----------------------------------
  **Python**           Application logic
  **Tkinter / ttk**    Desktop GUI
  **PostgreSQL**       Relational database
  **psycopg2**         PostgreSQL connection from Python
  **bcrypt**           Password hashing and verification
  **SQL / PL/pgSQL**   Database functions and procedures



## 🔑 Sample Login Accounts

The database script includes sample credentials for testing:

  Role       Username     Password
  ---------- ------------ ---------------
  User       `john_doe`   `password123`
  Admin      `admin`      `admin123`
  Employee   `emp`        `123`

These credentials are intended only for the sample/test database. Change
or remove them before using the project in a real environment.

------------------------------------------------------------------------

## 📋 Example Workflow

A typical workflow for testing the application:

``` text
1. Start PostgreSQL
        ↓
2. Run database.sql
        ↓
3. Configure database connection
        ↓
4. Run gui.py
        ↓
5. Sign in as Admin / Employee
        ↓
6. Create a bank user
        ↓
7. Create an account for that user
        ↓
8. Perform transactions
        ↓
9. Create or request loans
        ↓
10. Manage loan payments
```

------------------------------------------------------------------------

## 🎯 Project Goals

This project was developed to demonstrate practical experience with:

-   Python desktop application development
-   GUI design with Tkinter
-   PostgreSQL database design
-   Relational database concepts
-   CRUD operations
-   SQL functions and procedures
-   Role-based access
-   Password hashing
-   Transaction and loan management
-   Connecting a Python application to a relational database

------------------------------------------------------------------------

## 📌 Notes

This project was developed as a **team project for the Database course at university**.
It was collaboratively designed and implemented.

------------------------------------------------------------------------
