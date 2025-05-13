import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
from bcrypt import hashpw, gensalt
from datetime import datetime, timedelta
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
NEW_DB = os.getenv("NEW_DB")  # Database to create

def get_db_connection(dbname=NEW_DB):
    """
    Establish a connection to the PostgreSQL database.
    """
    conn = psycopg2.connect(
        dbname=dbname,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

def create_database():
    """
    Create the database if it doesn't exist.
    """
    # First try to connect without specifying a database (uses user's default)
    try:
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True  # Necessary for creating databases
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (NEW_DB,))
        exists = cursor.fetchone()
        
        if not exists:
            # Safely create the database using sql.Identifier to prevent SQL injection
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(NEW_DB))
            )
            print(f"Database '{NEW_DB}' created successfully!")
        else:
            print(f"Database '{NEW_DB}' already exists.")
            
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Error while creating database: {e}")

# Example usage:
create_database()
conn = get_db_connection()
# ... use the connection ...

def create_users_table():
    """ Creates the users table if it does not exist. """
    conn = get_db_connection()
    cursor = conn.cursor()

    create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            uid SERIAL PRIMARY KEY,
            uname VARCHAR(100) UNIQUE NOT NULL,
            phno VARCHAR(15) UNIQUE NOT NULL,
            mail VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(256) NOT NULL,  -- Hashed password stored here
            dob DATE NOT NULL,  -- Date of Birth added
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );


    -- Create a trigger function to update the modified_at field
    CREATE OR REPLACE FUNCTION update_modified_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.modified_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    -- Drop existing trigger (if any) and create a new one
    DROP TRIGGER IF EXISTS set_timestamp ON users;
    CREATE TRIGGER set_timestamp
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();
    """

    cursor.execute(create_table_query)
    conn.commit()
    cursor.close()
    conn.close()
    print("Users table with password field created successfully!")

def create_sessions_table():
    """ Creates the sessions table and ensures only active sessions are stored. """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    create_table_query = """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id SERIAL PRIMARY KEY,
        uid INT REFERENCES users(uid) ON DELETE CASCADE,
        token TEXT NOT NULL UNIQUE,
        ip_address VARCHAR(45),
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        status VARCHAR(10) CHECK (status = 'Active') DEFAULT 'Active'
    );"""
    
    cursor.execute(create_table_query)
    conn.commit()
    cursor.close()
    conn.close()
    print("Sessions table created successfully with automatic expired session cleanup!")

# ...existing code...

def create_billing_table():
    """ Creates the billing table if it does not exist. """
    conn = get_db_connection()
    cursor = conn.cursor()

    create_table_query = """
    CREATE TABLE IF NOT EXISTS billing (
        pid SERIAL PRIMARY KEY,
        current_id VARCHAR(255) UNIQUE,
        water_id VARCHAR(255) UNIQUE,
        amount_current DECIMAL(10,2),
        amount_water DECIMAL(10,2),
        status_current VARCHAR(10) CHECK (status_current IN ('Unpaid', 'Paid')) DEFAULT 'Unpaid',
        status_water VARCHAR(10) CHECK (status_water IN ('Unpaid', 'Paid')) DEFAULT 'Unpaid',
        phone_no VARCHAR(15) UNIQUE,
        today_date DATE,
        created_at TIMESTAMP DEFAULT NULL
    );
    """
    
    cursor.execute(create_table_query)
    conn.commit()
    cursor.close()
    conn.close()
    print("Billing table created successfully!")

def create_payments_table():
    """ Creates the payments table if it does not exist. """
    conn = get_db_connection()
    cursor = conn.cursor()

    create_table_query = """
    CREATE TABLE IF NOT EXISTS payments (
        payment_id SERIAL PRIMARY KEY,
        pid INT REFERENCES billing(pid) ON DELETE CASCADE,
        type VARCHAR(10) CHECK (type IN ('current', 'water')),
        amount DECIMAL(10,2),
        payment_status VARCHAR(10) CHECK (payment_status IN ('Success', 'Failed')) DEFAULT 'Success',
        paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(create_table_query)
    conn.commit()
    cursor.close()
    conn.close()
    print("Payments table created successfully!")


def insert_billing_data():
    """ Inserts data into the billing table if uid 50 does not exist. If uid 50 exists, updates all records to unpaid. """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if uid 50 exists in the billing table
    cursor.execute("SELECT EXISTS(SELECT 1 FROM billing WHERE pid = 48);")
    uid_50_exists = cursor.fetchone()[0]

    if not uid_50_exists:
        # Insert data if uid 50 does not exist
        insert_query = """
        INSERT INTO billing ( current_id, water_id, amount_current, amount_water, status_current, status_water,phone_no, created_at)
        VALUES 
            ('EB25020001', 'WB25020001', 100.50, 50.75, 'Unpaid', 'Unpaid',  '7411401601', '2025-03-02'),
            ('EB25020002', 'WB25020002', 200.00, 75.00, 'Unpaid', 'Unpaid',  '7411401602', '2025-03-02'),
            ('EB25020003', 'WB25020003', 150.25, 60.50, 'Unpaid', 'Unpaid',  '7411401603', '2025-03-02'),
            ('EB25020004', 'WB25020004', 175.75, 80.25, 'Unpaid', 'Unpaid',  '7411401604', '2025-03-02'),
            ('EB25020005', 'WB25020005', 125.00, 55.00, 'Unpaid', 'Unpaid',  '7411401605', '2025-03-02'),
            ('EB25020006', 'WB25020006', 110.50, 65.75, 'Unpaid', 'Unpaid',  '7411401606', '2025-03-02'),
            ('EB25020007', 'WB25020007', 210.00, 85.00, 'Unpaid', 'Unpaid',  '7411401607', '2025-03-02'),
            ('EB25020008', 'WB25020008', 160.25, 70.50, 'Unpaid', 'Unpaid',  '7411401608', '2025-03-02'),
            ('EB25020009', 'WB25020009', 185.75, 90.25, 'Unpaid', 'Unpaid',  '7411401609', '2025-03-02'),
            ( 'EB25020010', 'WB25020010', 135.00, 65.00, 'Unpaid', 'Unpaid', '7411401610',  '2025-03-02'),
            ( 'EB25020011', 'WB25020011', 120.50, 75.75, 'Unpaid', 'Unpaid', '7411401611',  '2025-03-02'),
            ( 'EB25020012', 'WB25020012', 220.00, 95.00, 'Unpaid', 'Unpaid', '7411401612',  '2025-03-02'),
            ( 'EB25020013', 'WB25020013', 170.25, 80.50, 'Unpaid', 'Unpaid', '7411401613',  '2025-03-02'),
            ( 'EB25020014', 'WB25020014', 195.75, 100.25, 'Unpaid', 'Unpaid', '7411401614',  '2025-03-02'),
            ( 'EB25020015', 'WB25020015', 145.00, 75.00, 'Unpaid', 'Unpaid',  '7411401615', '2025-03-02'),
            ( 'EB25020016', 'WB25020016', 130.50, 85.75, 'Unpaid', 'Unpaid',  '7411401616', '2025-03-02'),
            ( 'EB25020017', 'WB25020017', 230.00, 105.00, 'Unpaid', 'Unpaid', '7411401617',  '2025-03-02'),
            ( 'EB25020018', 'WB25020018', 180.25, 90.50, 'Unpaid', 'Unpaid',  '7411401618', '2025-03-02'),
            ( 'EB25020019', 'WB25020019', 205.75, 110.25, 'Unpaid', 'Unpaid', '7411401619',  '2025-03-02'),
            ( 'EB25020020', 'WB25020020', 155.00, 85.00, 'Unpaid', 'Unpaid',  '7411401620', '2025-03-02'),
            ( 'EB25020021', 'WB25020021', 140.50, 95.75, 'Unpaid', 'Unpaid',  '7411401621', '2025-03-02'),
            ( 'EB25020022', 'WB25020022', 240.00, 115.00, 'Unpaid', 'Unpaid', '7411401622',  '2025-03-02'),
            ( 'EB25020023', 'WB25020023', 190.25, 100.50, 'Unpaid', 'Unpaid', '7411401623',  '2025-03-02'),
            ( 'EB25020024', 'WB25020024', 215.75, 120.25, 'Unpaid', 'Unpaid', '7411401624',  '2025-03-02'),
            ( 'EB25020025', 'WB25020025', 165.00, 95.00, 'Unpaid', 'Unpaid',  '7411401625', '2025-03-02'),
            ( 'EB25020026', 'WB25020026', 150.50, 105.75, 'Unpaid', 'Unpaid', '7411401626',  '2025-03-02'),
            ( 'EB25020027', 'WB25020027', 250.00, 125.00, 'Unpaid', 'Unpaid', '7411401627',  '2025-03-02'),
            ( 'EB25020028', 'WB25020028', 200.25, 110.50, 'Unpaid', 'Unpaid', '7411401628',  '2025-03-02'),
            ( 'EB25020029', 'WB25020029', 225.75, 130.25, 'Unpaid', 'Unpaid', '7411401629',  '2025-03-02'),
            ( 'EB25020030', 'WB25020030', 175.00, 105.00, 'Unpaid', 'Unpaid', '7411401630',  '2025-03-02'),
            ( 'EB25020031', 'WB25020031', 160.50, 115.75, 'Unpaid', 'Unpaid', '7411401631',  '2025-03-02'),
            ( 'EB25020032', 'WB25020032', 260.00, 135.00, 'Unpaid', 'Unpaid', '7411401632',  '2025-03-02'),
            ( 'EB25020033', 'WB25020033', 210.25, 120.50, 'Unpaid', 'Unpaid', '7411401633',  '2025-03-02'),
            ( 'EB25020034', 'WB25020034', 235.75, 140.25, 'Unpaid', 'Unpaid', '7411401634',  '2025-03-02'),
            ( 'EB25020035', 'WB25020035', 185.00, 115.00, 'Unpaid', 'Unpaid', '7411401635',  '2025-03-02'),
            ( 'EB25020036', 'WB25020036', 170.50, 125.75, 'Unpaid', 'Unpaid', '7411401636',  '2025-03-02'),
            ( 'EB25020037', 'WB25020037', 270.00, 145.00, 'Unpaid', 'Unpaid', '7411401637',  '2025-03-02'),
            ( 'EB25020038', 'WB25020038', 220.25, 130.50, 'Unpaid', 'Unpaid', '7411401638',  '2025-03-02'),
            ( 'EB25020039', 'WB25020039', 245.75, 150.25, 'Unpaid', 'Unpaid', '7411401639',  '2025-03-02'),
            ( 'EB25020040', 'WB25020040', 195.00, 125.00, 'Unpaid', 'Unpaid', '7411401640',  '2025-03-02'),
            ( 'EB25020041', 'WB25020041', 180.50, 135.75, 'Unpaid', 'Unpaid', '7411401641',  '2025-03-02'),
            ( 'EB25020042', 'WB25020042', 280.00, 155.00, 'Unpaid', 'Unpaid', '7411401642',  '2025-03-02'),
            ( 'EB25020043', 'WB25020043', 230.25, 140.50, 'Unpaid', 'Unpaid', '7411401643',  '2025-03-02'),
            ( 'EB25020044', 'WB25020044', 255.75, 160.25, 'Unpaid', 'Unpaid', '7411401644',  '2025-03-02'),
            ( 'EB25020045', 'WB25020045', 205.00, 135.00, 'Unpaid', 'Unpaid', '7411401645',  '2025-03-02'),
            ( 'EB25020046', 'WB25020046', 190.50, 145.75, 'Unpaid', 'Unpaid', '7411401646',  '2025-03-02'),
            ( 'EB25020047', 'WB25020047', 290.00, 165.00, 'Unpaid', 'Unpaid', '7411401647',  '2025-03-02'),
            ( 'EB25020048', 'WB25020048', 240.25, 150.50, 'Unpaid', 'Unpaid', '7411401648',  '2025-03-02'),
            ( 'EB25020049', 'WB25020049', 265.75, 170.25, 'Unpaid', 'Unpaid', '7411401649',  '2025-03-02'),
            ( 'EB25020050', 'WB25020050', 215.00, 145.00, 'Unpaid', 'Unpaid', '7411401650',  '2025-03-02');
        """
        cursor.execute(insert_query)
        print("Data inserted successfully!")

        password = "123456"
        hashed_password = hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')

        # List of common Indian first and last names
        first_names = ["Amit", "Priya", "Rajesh", "Neha", "Vikram", "Anjali", "Sandeep", "Kiran", "Ravi", "Pooja",
                    "Arun", "Swati", "Rahul", "Divya", "Suresh", "Sneha", "Manoj", "Meena", "Abhishek", "Kavita"]

        last_names = ["Sharma", "Verma", "Gupta", "Patel", "Mehta", "Agarwal", "Bose", "Nair", "Choudhary", "Yadav",
                    "Reddy", "Pillai", "Desai", "Iyer", "Joshi", "Malhotra", "Saxena", "Trivedi", "Singh", "Kumar"]

        # Generate 25 unique users
        users = []
        used_names = set()  # To ensure unique names

        for i in range(2, 27):  # Start from 2 (0 & 1 are Admin & External)
            while True:
                first = random.choice(first_names)
                last = random.choice(last_names)
                full_name = f"{first} {last}"
                if full_name not in used_names:  # Ensure unique names
                    used_names.add(full_name)
                    break

            email = f"{first.lower()}.{last.lower()}{random.randint(10, 99)}@gmail.com"  # Unique email
            phone = f"98{random.randint(10000000, 99999999)}"  # Indian mobile number format
            created_at = (datetime.utcnow() - timedelta(days=random.randint(0, 15))).strftime('%Y-%m-%d %H:%M:%S')

            users.append((full_name, phone, email, hashed_password, '2001-01-01', created_at))

        # Convert users to SQL VALUES format
        users_values = ",\n    ".join(
            f"('{uname}', '{phno}', '{mail}', '{password}', '{dob}', '{created_at}')" 
            for uname, phno, mail, password, dob, created_at in users
        )

        # Insert query
        admin_insert_query = f"""
        INSERT INTO users ( uname, phno, mail, password, dob, created_at) 
        VALUES 
            ( 'Admin', '999999998', 'admin@gmail.com', '{hashed_password}', '2001-01-01', 
            '{(datetime.utcnow() - timedelta(days=random.randint(0, 15))).strftime('%Y-%m-%d %H:%M:%S')}'),

            ( 'External', '999999999', 'external@gmail.com', '{hashed_password}', '2001-01-01',
            '{(datetime.utcnow() - timedelta(days=random.randint(0, 15))).strftime('%Y-%m-%d %H:%M:%S')}'),

            {users_values};
        """

        cursor.execute(admin_insert_query)
        print("Admin, External, and 25 Indian users inserted successfully!")

    else:
        # Update all records to unpaid if uid 50 exists
        print("All records updated to unpaid!")

    conn.commit()
    cursor.close()
    conn.close()

def send_due_email():
    """
    Fetch users with due amounts and send email notifications for unpaid services only.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch the current date from the database
        cursor.execute("SELECT today_date from billing;")
        today = cursor.fetchone()[0]

        # Check if the date is between the 1st and 5th of the month
        if today.day < 1 or today.day > 5:
            return  # Exit if the date is not within the range

        # Fetch due users with separate amounts for unpaid current and water bills
        query = """
        SELECT 
            b.phone_no, 
            b.amount_current, 
            b.amount_water, 
            b.current_id, 
            b.water_id, 
            u.mail,
            u.uname,
            b.status_current,
            b.status_water
        FROM billing b
        LEFT JOIN users u ON b.phone_no = u.phno
        WHERE (b.status_current = 'Unpaid' OR b.status_water = 'Unpaid')
        AND b.today_date <= %s
        """
        cursor.execute(query, (today,))
        due_users = cursor.fetchall()

        if not due_users:
            return  # Exit if no due users are found

        # Email configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = os.getenv("sender_email")  # Fetch from .env file
        sender_password = os.getenv("sender_password")  # Fetch from .env file
        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)

        # Send emails to due users
        for phone_no, amount_current, amount_water, current_id, water_id, email, uname, status_current, status_water in due_users:
            if not email:
                continue  # Skip if no email is associated with the user

            # Generate payment links for unpaid services
            email_body = f"Dear {uname},\n\nThis is a reminder that your utility bills are due. Below are the details:\n\n"
            if status_current == "Unpaid":
                current_payment_link = f"http://127.0.0.1:8000/electricity_billing"
                email_body += f"- Current Bill: ₹{amount_current:.2f}\n  Pay here: {current_payment_link}\n\n"
            if status_water == "Unpaid":
                water_payment_link = f"http://127.0.0.1:8000/water_billing"
                email_body += f"- Water Bill: ₹{amount_water:.2f}\n  Pay here: {water_payment_link}\n\n"

            # Skip sending email if both services are already paid
            if status_current == "Paid" and status_water == "Paid":
                continue

            email_body += "Please log in to the utility billing portal and make the payment before the 5th of this month to avoid additional charges.\n\nThank you,\nUtility Services"

            # Create the email content
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = email
            msg["Subject"] = "Utility Bill Due Reminder"
            msg.attach(MIMEText(email_body, "plain"))

            # Send the email
            server.sendmail(sender_email, email, msg.as_string())

        # Close the SMTP server connection
        server.quit()

    except Exception as e:
        print(f"Error while sending due emails: {e}")
    finally:
        cursor.close()
        conn.close()
