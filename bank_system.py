import mysql.connector
import sys
from decimal import Decimal
import random
from datetime import datetime, timedelta

# --- 1. Database Connection ---
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",          # Your local MySQL username
            password="your_password",      # Your local MySQL password
            database="bank_db"    # Your local database name
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to local database: {err}")
        sys.exit(1)

# --- 2. Core Functions ---
def create_account():
    print("\n--- New Customer & Account Registration ---")
    
    name = input("Enter Full Name: ")
    phone = input("Enter Phone Number: ")
    address = input("Enter Address: ")
    dob = input("Enter Date of Birth (YYYY-MM-DD): ")
    
    pin = input("Set a 4-digit Security PIN: ")
    if len(pin) != 4 or not pin.isdigit():
        print("Error: PIN must be exactly 4 digits.")
        return
        
    try:
        initial_deposit = Decimal(input("Enter initial deposit amount: "))
        if initial_deposit < 0:
            print("Initial deposit cannot be negative.")
            return
    except ValueError:
        print("Invalid amount entered.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        conn.start_transaction()

        # Step A: Insert into Customer Table
        customer_query = "INSERT INTO customer (name, phone_num, address, dob) VALUES (%s, %s, %s, %s)"
        cursor.execute(customer_query, (name, phone, address, dob))
        cust_id = cursor.lastrowid

        # Step B: Create the Account linked to that cust_id
        account_query = "INSERT INTO accounts (cust_id, pin, balance) VALUES (%s, %s, %s)"
        cursor.execute(account_query, (cust_id, pin, initial_deposit))
        acc_num = cursor.lastrowid

        # Step C: Log the initial deposit
        if initial_deposit > 0:
            trans_query = """
                INSERT INTO transactions (acc_num, trans_type, amount, balance_after, description) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(trans_query, (acc_num, 'Initial Deposit', initial_deposit, initial_deposit, 'Account Opening'))

        conn.commit()
        print(f"\nSuccess! Customer ID: {cust_id}")
        print(f"Your Account Number is: {acc_num}")
        print("Please keep your PIN safe.")

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database Error: {err}")
    finally:
        cursor.close()
        conn.close()

def deposit():
    acc_no = input("Enter Account Number: ")
    amount = Decimal(input("Enter amount to deposit: "))
    
    if amount <= 0:
        print("Deposit amount must be greater than zero.")
        return

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT balance FROM accounts WHERE acc_num = %s", (acc_no,))
        result = cursor.fetchone()
        
        if not result:
            print("Account not found!")
            return

        new_balance = result['balance'] + amount

        cursor.execute("UPDATE accounts SET balance = %s WHERE acc_num = %s", (new_balance, acc_no))
        cursor.execute("INSERT INTO transactions (acc_num, trans_type, amount, balance_after, description) VALUES (%s, %s, %s, %s, %s)", 
                       (acc_no, 'Deposit', amount, new_balance, 'Cash Deposit'))
        
        conn.commit()
        print(f"\nSuccessfully deposited ${amount:.2f} into account {acc_no}.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def withdraw():
    acc_no = input("Enter Account Number: ")
    amount = Decimal(input("Enter amount to withdraw: "))
    
    if amount <= 0:
        print("Withdrawal amount must be greater than zero.")
        return

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT balance FROM accounts WHERE acc_num = %s", (acc_no,))
        result = cursor.fetchone()
        
        if not result:
            print("Account not found!")
            return
            
        current_balance = result['balance']
        
        if current_balance < amount:
            print(f"Insufficient funds! Current balance is ${current_balance:.2f}")
            return

        new_balance = current_balance - amount

        cursor.execute("UPDATE accounts SET balance = %s WHERE acc_num = %s", (new_balance, acc_no))
        cursor.execute("INSERT INTO transactions (acc_num, trans_type, amount, balance_after, description) VALUES (%s, %s, %s, %s, %s)", 
                       (acc_no, 'Withdrawal', amount, new_balance, 'Cash Withdrawal'))
        
        conn.commit()
        print(f"\nSuccessfully withdrew ${amount:.2f}. New balance: ${new_balance:.2f}")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def transfer_money():
    print("\n--- Transfer Funds ---")
    sender_acc = input("Enter your Account Number: ")
    pin = input("Enter your 4-digit PIN: ")
    receiver_acc = input("Enter Receiver's Account Number: ")
    
    if sender_acc == receiver_acc:
        print("Cannot transfer money to the same account.")
        return

    try:
        amount = Decimal(input("Enter amount to transfer: "))
    except:
        print("Invalid amount format.")
        return

    if amount <= 0:
        print("Transfer amount must be greater than zero.")
        return

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) 
    
    try:
        conn.start_transaction()

        cursor.execute("SELECT balance, pin FROM accounts WHERE acc_num = %s AND status = 'Active'", (sender_acc,))
        sender = cursor.fetchone()
        
        if not sender:
            print("Sender account not found or inactive.")
            return
        if sender['pin'] != pin:
            print("Incorrect PIN. Access Denied.")
            return
        if sender['balance'] < amount:
            print("Insufficient funds for transfer.")
            return

        cursor.execute("SELECT balance FROM accounts WHERE acc_num = %s AND status = 'Active'", (receiver_acc,))
        receiver = cursor.fetchone()
        
        if not receiver:
            print("Receiver account not found or inactive.")
            return

        new_sender_balance = sender['balance'] - amount
        new_receiver_balance = receiver['balance'] + amount

        cursor.execute("UPDATE accounts SET balance = %s WHERE acc_num = %s", (new_sender_balance, sender_acc))
        cursor.execute("UPDATE accounts SET balance = %s WHERE acc_num = %s", (new_receiver_balance, receiver_acc))

        cursor.execute("""
            INSERT INTO transactions (acc_num, trans_type, amount, balance_after, description) 
            VALUES (%s, 'Transfer Out', %s, %s, %s)
        """, (sender_acc, amount, new_sender_balance, f"Transferred to Acc {receiver_acc}"))

        cursor.execute("""
            INSERT INTO transactions (acc_num, trans_type, amount, balance_after, description) 
            VALUES (%s, 'Transfer In', %s, %s, %s)
        """, (receiver_acc, amount, new_receiver_balance, f"Received from Acc {sender_acc}"))

        conn.commit()
        print(f"\nSuccessfully transferred ${amount:.2f} to Account {receiver_acc}.")
        print(f"Your new balance is: ${new_sender_balance:.2f}")

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"\nTransaction Failed. Rolled back successfully. Error: {err}")
    finally:
        cursor.close()
        conn.close()

def apply_for_credit_card():
    print("\n=== CREDIT CARD APPLICATION ===")
    cust_id = input("Enter your Customer ID: ")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT SUM(balance) as total_bal FROM accounts WHERE cust_id = %s", (cust_id,))
        result = cursor.fetchone()
        
        if not result or result['total_bal'] is None:
            print("Error: No active accounts found for this Customer ID.")
            return
            
        total_balance = result['total_bal']
        
        if total_balance < 10000:
            print(f"Application Denied: Minimum balance of $10,000 required. Your balance: ${total_balance:.2f}")
            return

        credit_limit = total_balance * Decimal('0.5')
        
        card_num = "".join([str(random.randint(0, 9)) for _ in range(16)])
        cvv = "".join([str(random.randint(0, 9)) for _ in range(3)])
        expiry_date = (datetime.now() + timedelta(days=365*5)).date() 
        
        query = """
            INSERT INTO credit_cards (card_num, cust_id, card_type, credit_limit, expiry_date, cvv, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Active')
        """
        cursor.execute(query, (card_num, cust_id, 'Visa Platinum', credit_limit, expiry_date, cvv))
        conn.commit()
        
        print("\n--- Credit Card Issued Successfully! ---")
        print(f"Card Number: {card_num[:4]}-{card_num[4:8]}-{card_num[8:12]}-{card_num[12:]}")
        print(f"Credit Limit: ${credit_limit:.2f}")
        print(f"Expiry Date: {expiry_date} | CVV: {cvv}")
        
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database Error: {err}")
    finally:
        cursor.close()
        conn.close()

def use_credit_card():
    print("\n=== SWIPE CREDIT CARD ===")
    card_num = input("Enter 16-digit Card Number: ")
    cvv = input("Enter CVV: ")
    
    try:
        amount = Decimal(input("Enter transaction amount: "))
    except ValueError:
        print("Invalid amount.")
        return
        
    vendor = input("Enter Vendor/Store Name: ")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT credit_limit, status FROM credit_cards WHERE card_num = %s AND cvv = %s", (card_num, cvv))
        card = cursor.fetchone()

        if not card:
            print("Invalid Card Details.")
            return
        if card['status'] != 'Active':
            print("This card is blocked or inactive.")
            return
        
        if amount > card['credit_limit']:
            print("Transaction Declined: Insufficient Credit Limit.")
            return

        cursor.execute("""
            INSERT INTO card_transactions (card_num, amount, vendor_name) 
            VALUES (%s, %s, %s)
        """, (card_num, amount, vendor))
        
        conn.commit()
        print(f"Success! Paid ${amount:.2f} to {vendor}.")

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

def apply_for_loan():
    print("\n=== LOAN APPLICATION ===")
    cust_id = input("Enter your Customer ID: ")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT name FROM customer WHERE cust_id = %s", (cust_id,))
        customer = cursor.fetchone()
        
        if not customer:
            print("Customer not found. Please check your ID or register first.")
            return
            
        print(f"\nWelcome back, {customer['name']}!")
        
        cursor.execute("SELECT * FROM loan_type")
        loan_types = cursor.fetchall()
        
        if not loan_types:
            print("No loan products are currently available.")
            return
            
        print("\n--- Available Loan Products ---")
        for lt in loan_types:
            print(f"ID: {lt['loan_type_id']} | Type: {lt['type_name']:<15} | Default Rate: {lt['default_rate']}%")
            
        loan_type_id = input("\nEnter the ID of the loan you want to apply for: ")
        amount = input("Enter loan amount requested: ")
        months = input("Enter loan term (in months): ")
        
        cursor.execute("SELECT default_rate FROM loan_type WHERE loan_type_id = %s", (loan_type_id,))
        selected_type = cursor.fetchone()
        
        if not selected_type:
            print("Invalid Loan Type ID.")
            return
            
        rate = selected_type['default_rate']
        
        insert_query = """
            INSERT INTO loans (cust_id, loan_type_id, amount, rate, term_months, start_date, status)
            VALUES (%s, %s, %s, %s, %s, CURDATE(), 'Pending')
        """
        cursor.execute(insert_query, (cust_id, loan_type_id, amount, rate, months))
        conn.commit()
        
        loan_id = cursor.lastrowid
        print(f"\nSuccess! Your loan application for ${float(amount):.2f} has been submitted.")
        print(f"Application ID: {loan_id} | Status: Pending Approval")
        
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database Error: {err}")
    except ValueError:
        print("Invalid input format for amount or months. Please enter numbers only.")
    finally:
        cursor.close()
        conn.close()

def transaction_history():
    acc_no = input("Enter Account Number: ")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT trans_type, amount, balance_after, trans_date FROM transactions WHERE acc_num = %s ORDER BY trans_date DESC", (acc_no,))
        records = cursor.fetchall()
        
        if not records:
            print("No transactions found or account does not exist.")
            return
            
        print(f"\n--- Transaction History for Account {acc_no} ---")
        for record in records:
            print(f"{record['trans_date']} | {record['trans_type']:<15} | Amount: ${record['amount']:.2f} | Balance: ${record['balance_after']:.2f}")
        print("---------------------------------------------")
            
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

# --- 3. Admin & Staff Functions ---
def admin_panel():
    print("\n=== SYSTEM LOGIN ===")
    emp_id = input("Enter Employee ID: ")
    password = input("Enter Password: ")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = "SELECT name, position FROM employees WHERE emp_id = %s AND password = %s"
        cursor.execute(query, (emp_id, password))
        employee = cursor.fetchone()
        
        if not employee:
            print("Access Denied: Invalid Employee ID or Password.")
            return

        if employee['position'] not in ['Manager', 'Admin']:
            print(f"Access Denied: Role '{employee['position']}' is unauthorized.")
            return

        print(f"\nLogin Successful. Welcome, {employee['name']}.")
        
        while True:
            print("\n=== ADMIN DASHBOARD ===")
            print("1. View All Customers & Accounts")
            print("2. Manage Pending Loans")
            print("3. View Branch Directory")
            print("4. View Staff by Branch")
            print("5. Exit Admin Panel")
            
            choice = input("Enter choice (1-5): ")
            
            if choice == '1': 
                admin_view_accounts()
            elif choice == '2': 
                admin_manage_loans()
            elif choice == '3': 
                view_branch_details()
            elif choice == '4': 
                view_staff_by_branch()
            elif choice == '5': 
                print("Exiting Admin Panel...")
                break
            else:
                print("Invalid choice.")

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    finally:
        cursor.close()
        conn.close()

def admin_view_accounts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT a.acc_num, c.name, a.balance, a.status 
            FROM accounts a
            JOIN customer c ON a.cust_id = c.cust_id
            ORDER BY a.acc_num
        """
        cursor.execute(query)
        accounts = cursor.fetchall()
        
        total_liquidity = Decimal('0.00')
        
        print("\n--- Master Accounts List ---")
        for acc in accounts:
            print(f"Acc: {acc['acc_num']} | Owner: {acc['name']:<15} | Status: {acc['status']} | Balance: ${acc['balance']:.2f}")
            total_liquidity += acc['balance']
            
        print("-" * 50)
        print(f"TOTAL BANK LIQUIDITY: ${total_liquidity:.2f}")
        
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    finally:
        cursor.close()
        conn.close()

def admin_manage_loans():
    print("\n--- PENDING LOAN APPLICATIONS ---")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = """
            SELECT l.loan_id, c.name, l.amount, l.rate, l.term_months, l.start_date
            FROM loans l
            JOIN customer c ON l.cust_id = c.cust_id
            WHERE l.status = 'Pending'
        """
        cursor.execute(query)
        pending_loans = cursor.fetchall()
        
        if not pending_loans:
            print("No pending loan applications found.")
            return

        for loan in pending_loans:
            print(f"ID: {loan['loan_id']} | Customer: {loan['name']} | Amount: ${loan['amount']:.2f} | Term: {loan['term_months']} months")

        loan_id = input("\nEnter Loan ID to Approve/Reject (or 'c' to cancel): ")
        if loan_id.lower() == 'c': return

        action = input("Type 'A' to Approve or 'R' to Reject: ").upper()
        
        if action == 'A':
            status_update = 'Approved'
        elif action == 'R':
            status_update = 'Rejected'
        else:
            print("Invalid action.")
            return

        cursor.execute("UPDATE loans SET status = %s WHERE loan_id = %s", (status_update, loan_id))
        conn.commit()
        print(f"\nLoan ID {loan_id} has been {status_update}.")

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database Error: {err}")
    finally:
        cursor.close()
        conn.close()

def view_branch_details():
    print("\n--- BANK BRANCH DIRECTORY ---")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM bank_branch")
        branches = cursor.fetchall()
        
        if not branches:
            print("No branches registered in the system.")
            return

        for b in branches:
            print(f"ID: {b['branch_id']} | Name: {b['branch_name']} | IFSC: {b['branch_ifsc']}")
            print(f"   Location: {b['branch_address']}, {b['city']}, {b['state']}")
            print("-" * 40)
            
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    finally:
        cursor.close()
        conn.close()

def view_staff_by_branch():
    branch_id = input("\nEnter Branch ID to view staff: ")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = """
            SELECT e.emp_id, e.name, e.position, e.salary, m.name AS manager_name
            FROM employees e
            LEFT JOIN employees m ON e.manager_id = m.emp_id
            WHERE e.branch_id = %s
        """
        cursor.execute(query, (branch_id,))
        staff = cursor.fetchall()
        
        if not staff:
            print("No employees found for this branch.")
            return

        print(f"\n--- Staff List for Branch ID {branch_id} ---")
        total_payroll = 0
        for s in staff:
            manager = s['manager_name'] if s['manager_name'] else "None (Top Level)"
            print(f"ID: {s['emp_id']} | {s['name']} ({s['position']}) | Manager: {manager}")
            total_payroll += s['salary']
        
        print(f"\nMonthly Branch Payroll Expense: ${total_payroll:,.2f}")
            
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    finally:
        cursor.close()
        conn.close()

# --- 4. Main CLI Loop ---
def main():
    while True:
        print("\n=== BANK MANAGEMENT SYSTEM (LOCAL) ===")
        print("1. Create New Account")
        print("2. Deposit Money")
        print("3. Withdraw Money")
        print("4. Transfer Funds")
        print("5. Apply for a Loan")
        print("6. Apply for a Credit Card")
        print("7. Swipe Credit Card (Make Purchase)")
        print("8. View Transaction History")
        print("9. Admin Dashboard (Staff Only)")
        print("10. Exit")
        
        choice = input("Enter your choice (1-10): ")
        
        if choice == '1': create_account()
        elif choice == '2': deposit()
        elif choice == '3': withdraw()
        elif choice == '4': transfer_money()
        elif choice == '5': apply_for_loan()
        elif choice == '6': apply_for_credit_card()
        elif choice == '7': use_credit_card()
        elif choice == '8': transaction_history()
        elif choice == '9': admin_panel()
        elif choice == '10':
            print("Exiting system. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 10.")

if __name__ == "__main__":
    main()