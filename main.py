from route import *
import smtplib
from payment import *
from payment import router  # Import the router from payment.py
from fastapi.responses import RedirectResponse  # Import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware  # Import SessionMiddleware
import json

# Include the payment router in the app
app.include_router(router, prefix="/api", tags=["payment"])  # Add a prefix like /api if needed


# Table creation Functions

create_users_table()
create_sessions_table()
create_billing_table()
create_payments_table()
insert_billing_data()


# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# User Registration Model
class UserCreate(BaseModel):
    uname: str
    phno: str
    mail: EmailStr
    password: str
    dob: date  # Added Date of Birth field

# Hash Password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)




# Define an access key for security
ACCESS_KEY = "your-secret-key"
# Email configuration (replace with real credentials)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-email@gmail.com"  # Your sender email
SMTP_PASSWORD = "your-app-password"  # Use an app password for security

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str

# Dependency to check access key
def check_access_key(authorization: str = Header(None)):
    if authorization != f"Bearer {ACCESS_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/send-email/")
async def send_email(form: ContactForm, auth: str = Depends(check_access_key)):
    recipient_email = "sr7411401697@gmail.com"  # Target email

    # Email message format
    email_body = f"""
    Subject: New Contact Form Submission

    Name: {form.name}
    Email: {form.email}
    Message: {form.message}
    """

    try:
        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, recipient_email, email_body)
        server.quit()
        return {"detail": "Email sent successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# 🔹 REGISTER USER
@app.post("/register")
def register_user(user: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        hashed_password = hash_password(user.password)
        cursor.execute(
            """
            INSERT INTO users (uname, phno, mail, password, dob) 
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user.uname, user.phno, user.mail, hashed_password, user.dob)
        )
        conn.commit()
        return {"message": "User registered successfully!"}
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Phone number or email already registered")
    finally:
        cursor.close()
        conn.close()


# User Login Model
class UserLogin(BaseModel):
    mail: EmailStr
    password: str

# Verify Password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 🔹 LOGIN USER & CREATE SESSION
@app.post("/login")
async def login_user(request: Request, user: UserLogin):
    """
    Handle user login and redirect to appropriate pages based on credentials.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if the email belongs to admin or external user
        cursor.execute("SELECT uid, uname, password FROM users WHERE mail = %s", (user.mail,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=400, detail="Invalid email or password")

        uid, uname, hashed_password = result

        # Verify password
        if not verify_password(user.password, hashed_password):
            raise HTTPException(status_code=400, detail="Invalid email or password")

        # Check if the user is admin
        if user.mail == "admin@gmail.com":
            session_token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=1)

            # Insert admin session into the sessions table
            cursor.execute(
                """
                INSERT INTO sessions (uid, token, expires_at) 
                VALUES (%s, %s, %s)
                """,
                (uid, session_token, expires_at)
            )
            conn.commit()

            # Store session data
            request.session["session_token"] = session_token
            request.session["user_name"] = "Admin"
            return RedirectResponse(url="/admin/home", status_code=303)

        # Check if the user is external
        if user.mail == "external@gmail.com":
            session_token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=1)

            # Insert external user session into the sessions table
            cursor.execute(
                """
                INSERT INTO sessions (uid, token, expires_at) 
                VALUES (%s, %s, %s)
                """,
                (uid, session_token, expires_at)
            )
            conn.commit()

            # Store session data
            request.session["session_token"] = session_token
            request.session["user_name"] = "External"
            return RedirectResponse(url="/external/billing", status_code=303)

        # Handle normal user login
        session_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Create a session for the user
        cursor.execute(
            """
            INSERT INTO sessions (uid, token, expires_at) 
            VALUES (%s, %s, %s)
            """,
            (uid, session_token, expires_at)
        )
        conn.commit()

        # Store session data
        request.session["session_token"] = session_token
        request.session["user_name"] = uname  # Store the username in session

        return RedirectResponse(url="/", status_code=303)
    finally:
        cursor.close()
        conn.close()

@app.get("/logout")
def logout_user(request: Request):
    session_token = request.session.get("session_token")
    if session_token:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM sessions WHERE token = %s", (session_token,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    
    request.session.clear()

    # Return an HTMLResponse with a JavaScript alert and redirect
    return HTMLResponse(content=f"""
        <script>
            alert("Logged out successfully!");
            window.location.href = "/";  // Redirect to the home page
        </script>
    """)

# Function to check active session
def get_current_user(request: Request):
    session_token = request.session.get("session_token")
    
    if not session_token:
        print("DEBUG: No session token found in request.")
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT uid FROM sessions WHERE token = %s ", (session_token,))
        result = cursor.fetchone()        
        if not result:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        return result[0]
    finally:
        cursor.close()
        conn.close()

# Billing Response Model
class BillingResponse(BaseModel):
    billing_id: int
    uid: int
    month: str
    electric_bill: float
    water_bill: float
    total: float

# 🔹 FETCH BILLING DETAILS (Only for Authenticated User)
@app.get("/billing", response_model=list[BillingResponse])
def get_billing(request: Request):
    user_id = get_current_user(request)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM billing WHERE uid = %s", (user_id,))
        records = cursor.fetchall()

        if not records:
            raise HTTPException(status_code=404, detail="No billing records found")

        return [
            {
                "billing_id": record[0],
                "uid": record[1],
                "month": record[2],
                "electric_bill": record[3],
                "water_bill": record[4],
                "total": record[3] + record[4]
            }
            for record in records
        ]
    finally:
        cursor.close()
        conn.close()

# 🔹 FETCH BILLING DETAILS OF PREVIOUS MONTH
@app.get("/user/payment-history", response_class=JSONResponse)
async def get_payment_history(request: Request):
    """
    Fetch payment history for the authenticated user.
    """
    # Get the authenticated user's ID
    user_id = get_current_user(request)

    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 1: Get the phone number of the user using uid
        cursor.execute("SELECT phno FROM users WHERE uid = %s", (user_id,))
        phone_number = cursor.fetchone()

        if not phone_number:
            raise HTTPException(status_code=404, detail="Phone number not found for the user.")

        phone_number = phone_number[0]

        # Step 2: Get the pid from the billing table using the phone number
        cursor.execute("SELECT pid FROM billing WHERE phone_no = %s", (phone_number,))
        pid = cursor.fetchone()

        if not pid:
            raise HTTPException(status_code=404, detail="No billing record found for the user's phone number.")

        pid = pid[0]

        # Step 3: Fetch payment history using the pid
        query = """
        SELECT 
            p.payment_id,
            p.amount,
            p.payment_status,
            p.paid_at,
            p.type,
            b.current_id,
            b.water_id
        FROM 
            payments p
        LEFT JOIN 
            billing b ON p.pid = b.pid
        WHERE 
            p.pid = %s
        ORDER BY 
            p.paid_at DESC;
        """
        cursor.execute(query, (pid,))
        payment_history = cursor.fetchall()

        # Close the database connection
        cursor.close()
        conn.close()

        # Format the response
        if not payment_history:
            return JSONResponse({"message": "No payment history found for the user."}, status_code=404)

        response = {
            "user_id": user_id,
            "phone_number": phone_number,
            "payment_history": [
                {
                    "payment_id": record[0],
                    "amount": float(record[1]),  # Convert Decimal to float
                    "payment_status": record[2],
                    "type": record[4],
                    "paid_at": record[3].strftime('%Y-%m-%d %H:%M:%S') if record[3] else None,
                    "current_id": record[5],
                    "water_id": record[6]
                }
                for record in payment_history
            ]
        }

        return JSONResponse(response, status_code=200)

    except Exception as e:
        print(f"❌ Error fetching payment history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching payment history.")

############################# Billing API #############################

# reCAPTCHA Secret Key (Replace with your actual key)
class PaymentRequest(BaseModel):
    water_id: str  # Assuming water_id is a string (if it's numeric, change it to int)

class PaymentResponse(BaseModel):
    payment_id: int
    amount: float
    payment_status: str
    paid_at: str


@app.post("/api/get-payment-status", response_model=PaymentResponse)
async def get_payment_status(request: PaymentRequest):
    """Fetch payment status using water ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pid, amount_water, status_water, created_at
        FROM billing 
        WHERE water_id = %s
    """, (request.water_id,))
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="No payment record found")

    return PaymentResponse(
        payment_id=result[0],
        amount=result[1],
        payment_status=result[2],
        paid_at=result[3].strftime('%Y-%m-%d %H:%M:%S') if result[3] else "N/A"
    )


class ElectricityPaymentRequest(BaseModel):
    current_id: str  # Assuming current_id is a string

class ElectricityPaymentResponse(BaseModel):
    payment_id: int
    amount: float
    payment_status: str
    paid_at: str

@app.post("/api/get-electricity-status", response_model=ElectricityPaymentResponse)
async def get_electricity_status(request: ElectricityPaymentRequest):
    """Fetch payment status using current ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pid, amount_current, status_current, created_at
        FROM billing 
        WHERE current_id = %s
    """, (request.current_id,))
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="No payment record found")

    return ElectricityPaymentResponse(
        payment_id=result[0],
        amount=result[1],
        payment_status=result[2],
        paid_at=result[3].strftime('%Y-%m-%d %H:%M:%S') if result[3] else "N/A"
    )

class PaymentRequest(BaseModel):
    water_id: str  # Assuming water_id is a string (if it's numeric, change it to int)


@app.get("/water-bill-status", response_class=JSONResponse)
async def water_bill_status(request: Request):
    """
    Fetch water bill status for the authenticated user.
    """
    # Check if the user is authenticated
    session_token = request.session.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 1: Fetch the user's phone number using the session token
        cursor.execute("""
            SELECT u.phno
            FROM users u
            INNER JOIN sessions s ON u.uid = s.uid
            WHERE s.token = %s
        """, (session_token,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        phone_number = result[0]

        # Step 2: Fetch the water bill status and water_id using the phone number
        cursor.execute("""
            SELECT amount_water, status_water, created_at, water_id
            FROM billing
            WHERE phone_no = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (phone_number,))
        bill = cursor.fetchone()

        if not bill:
            raise HTTPException(status_code=404, detail="No billing record found")

        amount_water, status_water, created_at, water_id = bill

        # Step 3: Check the status and return the appropriate response
        if status_water == "Paid":
            return JSONResponse({"message": "Water bill is already paid. No action needed."}, status_code=200)

        # If unpaid, return the amount, date, and water_id
        return JSONResponse({
            "phone_number": phone_number,
            "amount": float(amount_water),
            "status": status_water,
            "date": created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else None,
            "water_id": water_id
        }, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/electric-bill-status", response_class=JSONResponse)
async def electric_bill_status(request: Request):
    """
    Fetch electricity bill status for the authenticated user.
    """
    # Check if the user is authenticated
    session_token = request.session.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 1: Fetch the user's phone number using the session token
        cursor.execute("""
            SELECT u.phno
            FROM users u
            INNER JOIN sessions s ON u.uid = s.uid
            WHERE s.token = %s
        """, (session_token,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        phone_number = result[0]

        # Step 2: Fetch the electricity bill status and current_id using the phone number
        cursor.execute("""
            SELECT amount_current, status_current, created_at, current_id
            FROM billing
            WHERE phone_no = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (phone_number,))
        bill = cursor.fetchone()

        if not bill:
            raise HTTPException(status_code=404, detail="No billing record found")

        amount_current, status_current, created_at, current_id = bill

        # Step 3: Check the status and return the appropriate response
        if status_current == "Paid":
            return JSONResponse({"message": "Electricity bill is already paid. No action needed."}, status_code=200)

        # If unpaid, return the amount, date, and current_id
        return JSONResponse({
            "phone_number": phone_number,
            "amount": float(amount_current),
            "status": status_current,
            "date": created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else None,
            "current_id": current_id
        }, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
################### externalUser Anil Work####################
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
import random
import psycopg2
from fastapi.responses import JSONResponse, RedirectResponse


class UpdateBillingRequest(BaseModel):
    date: str  # Date in 'YYYY-MM-DD' format

class UpdateBillingResponse(BaseModel):
    success: bool
    message: str

@app.post("/api/update-billing", response_model=UpdateBillingResponse)
async def update_billing(request: UpdateBillingRequest, session: Request):
    """Update all PID records with random amounts, a selected date, and set statuses to 'Unpaid'"""
    # Check if the user is authenticated and is 'externaluser@gmail.com'
    session_token = session.session.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Verify if the session belongs to 'externaluser@gmail.com'
        cursor.execute("""
            SELECT u.mail
            FROM users u
            INNER JOIN sessions s ON u.uid = s.uid
            WHERE s.token = %s
        """, (session_token,))
        result = cursor.fetchone()

        if not result or result[0] != "external@gmail.com":
            raise HTTPException(status_code=403, detail="Access forbidden")

        # Validate the date format
        try:
            selected_date = datetime.strptime(request.date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use 'YYYY-MM-DD'.")

        # Ensure the selected date is not less than the current date in the database
        cursor.execute("SELECT MAX(created_at) FROM billing;")
        max_date = cursor.fetchone()[0]
        if max_date and selected_date < max_date.date():
            raise HTTPException(status_code=400, detail="Selected date cannot be earlier than the latest billing date.")

        # Fetch all PIDs from the billing table
        cursor.execute("SELECT pid, amount_current, amount_water FROM billing;")
        pids = cursor.fetchall()

        if not pids:
            raise HTTPException(status_code=404, detail="No PIDs found in the billing table.")

        # Update each PID with new amounts (added to existing amounts), the selected date, and set statuses to 'Unpaid'
        for pid, current_amount, water_amount in pids:
            new_amount_current = round(float(current_amount) + random.uniform(100, 200), 2)
            new_amount_water = round(float(water_amount) + random.uniform(100, 200), 2)

            update_query = """
            UPDATE billing
            SET amount_current = %s, amount_water = %s, created_at = %s, 
                status_current = 'Unpaid', status_water = 'Unpaid'
            WHERE pid = %s;
            """
            cursor.execute(update_query, (new_amount_current, new_amount_water, selected_date, pid))

        conn.commit()
        return UpdateBillingResponse(
            success=True,
            message="All PID data updated successfully with statuses set to 'Unpaid'!"
        )

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

# Get payment history for external user
class PaymentHistoryResponse(BaseModel):
    user_id: int
    phone_number: str
    payment_history: list[dict]

@app.get("/user/payment-history", response_model=PaymentHistoryResponse)
def get_current_external_user(request: Request):
    """
    Retrieve the current external user based on the session token.
    """
    session_token = request.session.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT u.uid, u.phno
            FROM users u
            INNER JOIN sessions s ON u.uid = s.uid
            WHERE s.token = %s AND u.mail = 'external@gmail.com'
        """, (session_token,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=403, detail="Access forbidden")

        return {"uid": result[0], "phone": result[1]}
    finally:
        cursor.close()
        conn.close()

async def get_payment_history(user: dict = Depends(get_current_external_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT payment_id, amount, status, paid_at, bill_type, bill_id
            FROM payments
            WHERE user_id = %s
            ORDER BY paid_at DESC
            LIMIT 50
        """, (user["uid"],))
        
        payment_history = [
            {
                "payment_id": row[0],
                "amount": float(row[1]),
                "payment_status": row[2],
                "paid_at": row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else None,
                "type": row[4],
                "bill_id": row[5]
            }
            for row in cursor.fetchall()
        ]

        return {
            "user_id": user["uid"],
            "phone_number": user["phone"],
            "payment_history": payment_history
        }
    finally:
        cursor.close()
        conn.close()

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request, Depends
from datetime import datetime
import psycopg2

# Pydantic model for adding billing data
class AddBillingRequest(BaseModel):
    current_id: str
    water_id: str
    amount_current: float
    amount_water: float
    phone_no: str

class AddBillingResponse(BaseModel):
    success: bool
    message: str

@app.post("/api/add-billing", response_model=AddBillingResponse)
async def add_billing(request: AddBillingRequest, session: Request):
    """
    Add new billing data. Only accessible by the external user.
    """
    # Check if the user is authenticated and is 'external@gmail.com'
    session_token = session.session.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Verify if the session belongs to 'external@gmail.com'
        cursor.execute("""
            SELECT u.mail
            FROM users u
            INNER JOIN sessions s ON u.uid = s.uid
            WHERE s.token = %s
        """, (session_token,))
        result = cursor.fetchone()

        if not result or result[0] != "external@gmail.com":
            raise HTTPException(status_code=403, detail="Access forbidden")

        # Insert new billing data
        insert_query = """
        INSERT INTO billing (current_id, water_id, amount_current, amount_water, status_current, status_water, phone_no, created_at)
        VALUES (%s, %s, %s, %s, 'Unpaid', 'Unpaid', %s, %s)
        """
        cursor.execute(insert_query, (
            request.current_id,
            request.water_id,
            request.amount_current,
            request.amount_water,
            request.phone_no,
            datetime.utcnow()
        ))
        conn.commit()

        return AddBillingResponse(
            success=True,
            message="New billing data added successfully!"
        )

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()
############################################ ADMIn WOrk ####################################
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.get("/dashboard/stats")
def get_dashboard_stats():
    try:
        conn = get_db_connection()  # Establish connection
        cursor = conn.cursor()

        # Fetch total users
        cursor.execute("SELECT COUNT(*) FROM users;")
        total_users = cursor.fetchone()[0]

        # Fetch active users (users with active session)
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'Active';")
        active_users = cursor.fetchone()[0]

        # Fetch pending bills count (unpaid current + unpaid water)
        cursor.execute("SELECT COUNT(*) FROM billing WHERE status_current = 'Unpaid' OR status_water = 'Unpaid';")
        pending_bills = cursor.fetchone()[0]

        # Calculate total revenue (sum of paid bills)
        cursor.execute("""
            SELECT COALESCE(SUM(amount_current), 0) + COALESCE(SUM(amount_water), 0)
            FROM billing
            WHERE status_current = 'Paid' OR status_water = 'Paid';
        """)
        total_revenue = cursor.fetchone()[0]

        cursor.close()
        conn.close()  # Close the connection

        return {
            "total_users": total_users,
            "active_users": active_users,
            "pending_bills": pending_bills,
            "total_revenue": total_revenue
        }
    except Exception as e:
        return {"error": str(e)}
    
import psycopg2
from fastapi import FastAPI
from typing import Literal

@app.get("/user-registration-trend")
def user_registration_trend(interval: Literal["daily", "weekly", "monthly"] = "daily"):
    try:
        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query based on interval
        if interval == "daily":
            query = """
                SELECT DATE(created_at) AS period, COUNT(*) AS total_users
                FROM users
                GROUP BY DATE(created_at)
                ORDER BY period;
            """
        elif interval == "weekly":
            query = """
                SELECT DATE_TRUNC('week', created_at)::DATE AS period, COUNT(*) AS total_users
                FROM users
                GROUP BY DATE_TRUNC('week', created_at)
                ORDER BY period;
            """
        elif interval == "monthly":
            query = """
                SELECT DATE_TRUNC('month', created_at)::DATE AS period, COUNT(*) AS total_users
                FROM users
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY period;
            """

        # Execute query
        cursor.execute(query)
        result = cursor.fetchall()

        # Convert results to JSON format
        data = [{"period": str(row[0]), "total_users": row[1]} for row in result]

        return {"interval": interval, "data": data}

    except Exception as e:
        return {"error": str(e)}

    finally:
        # Ensure connection is closed properly
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Pydantic model for User
from pydantic import BaseModel
from typing import List
# Pydantic model for User
class User(BaseModel):
    uid: int
    uname: str
    phno: str
    mail: str
    dob: str  # Make sure the dob is returned as a string
    created_at: str
    modified_at: str

    # Convert datetime.date to string format
    @classmethod
    def from_db_row(cls, row):
        # Ensure dob is returned as string formatted as 'YYYY-MM-DD'
        return cls(
            uid=row[0],
            uname=row[1],
            phno=row[2],
            mail=row[3],
            dob=row[4].strftime('%Y-%m-%d'),  # Convert to string
            created_at=row[5].strftime('%Y-%m-%d %H:%M:%S'),
            modified_at=row[6].strftime('%Y-%m-%d %H:%M:%S')
        )

# Endpoint to fetch all user details for admin panel
@app.get("/admin/users", response_model=List[User])
def get_user_details():
    try:
        conn = get_db_connection()  # Establish connection
        cursor = conn.cursor()
        
        # SQL Query to fetch user details
        cursor.execute("SELECT uid, uname, phno, mail, dob, created_at, modified_at FROM users;")
        
        # Fetch all user records
        users = cursor.fetchall()
        
        # Closing cursor and connection
        cursor.close()
        conn.close()
        
        # Return the fetched data in a structured format
        return [User.from_db_row(user) for user in users]
    except Exception as e:
        return {"error": str(e)}
    
    
    
# Billing Data Model
class Billing(BaseModel):
    pid: int
    current_id: str
    water_id: str
    amount_current: float
    amount_water: float
    status_current: str
    status_water: str
    phone_no: str
    created_at: str

@app.get("/admin/billing", response_model=List[Billing])
def get_billing_data():
    try:
        conn = get_db_connection()  # Establish connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM billing;")  # Query all billing data
        rows = cursor.fetchall()

        billing_data = []
        for row in rows:
            billing_data.append({
                "pid": row[0],
                "current_id": row[1],
                "water_id": row[2],
                "amount_current": row[3],
                "amount_water": row[4],
                "status_current": row[5],
                "status_water": row[6],
                "phone_no": row[7],
                "created_at": row[8].strftime('%Y-%m-%d %H:%M:%S') if row[8] else None,
            })
        
        cursor.close()
        conn.close()
        
        return billing_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/admin/update-billing-date")
async def update_billing_date(request: Request, date: dict):
    """
    Update the today_date column in the billing table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Extract the date from the request
        selected_date = date.get("date")
        if not selected_date:
            raise HTTPException(status_code=400, detail="Date is required.")

        # Update the today_date column in the billing table
        update_query = """
        UPDATE billing
        SET today_date = %s
        """
        cursor.execute(update_query, (selected_date,))
        conn.commit()
        send_due_email()
        
        return {"message": f"Billing date updated to {selected_date} successfully!"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()
