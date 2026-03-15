# Bank Management System 
A robust, CLI-based banking application built with Python and MySQL. This project demonstrates full CRUD operations, ACID-compliant transactions, and Role-Based Access Control (RBAC) based on a formal ER diagram.

## 🚀 Features
- **Core Banking:** Account creation, deposits, withdrawals, and inter-bank fund transfers with transaction rollbacks.

- **Loan Management:** Customers can apply for specific loan products; Admins can approve or reject pending applications.

- **Credit Card System:** Logic-based card issuance (minimum balance check) and a simulated "swipe" transaction tracker.

- **Admin Dashboard:** Secure staff-only gateway to manage loans, view bank liquidity, and monitor branch/employee details.

## 🛠️ Technical Stack
- **Language:** Python 

- **Database:** MySQL

- **Libraries:** mysql-connector-python, decimal, datetime

## 📁 Database Schema
The system is built on a normalized relational schema including:

customer & accounts (1:N Relationship)

transactions (Linked to Accounts)

loans & loan_type

employees (Self-referencing for Manager hierarchy) & bank_branch

## 🔧 Installation & Setup
- **Clone the repository:**

```Bash
git clone https://github.com/yourusername/bank-management-system.git
-**Install dependencies:**

Bash
pip install mysql-connector-python
- **Database Setup:**

Open your MySQL terminal.

Run the provided database_setup.sql script to build the tables and seed default data.

- **Configure Connection:**

Update the get_db_connection() function in bank_system.py with your local MySQL user and password.

- **Run the App:**

Bash
python bank_system.py
🛡️ Security & Future Improvements
As a modular MVP, this project currently uses plain-text PINs and passwords for ease of demonstration. Future iterations will include:

Password Hashing: Implementing bcrypt for secure credential storage.

Connection Pooling: Optimizing database performance for high-traffic environments.

GUI/Web Interface: Transitioning from CLI to a Flask or Django-based web dashboard.

IoT Authentication: Integrating biometric or hardware-based MFA for transaction security.