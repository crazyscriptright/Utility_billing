# payment.py
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import razorpay
import os
from dotenv import load_dotenv
from database import get_db_connection
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import razorpay
from pydantic import BaseModel
from main import app
# Load API keys from .env
load_dotenv()
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    raise ValueError("❌ Razorpay API keys missing. Check your .env file.")

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Define OrderRequest Pydantic model
class OrderRequest(BaseModel):
    amount: int
    currency: Optional[str] = "INR"  # Default to INR
    userid: int

# Set up router and templates
router = APIRouter()
templates = Jinja2Templates(directory="templates")
class OrderRequest(BaseModel):
    amount: float
    userid: int

@app.post("/api/create_order/")
async def create_order(order: OrderRequest):
    print("✅ Received Payment Request:", order.dict()) 
    
    try:
        order_data = {
            "amount": int(order.amount * 100),  # Convert to paise
            "currency": "INR",
            "payment_capture": 1  
        }
        
        print("🛒 Sending Order Request to Razorpay:", order_data)
        created_order = razorpay_client.order.create(order_data)
        
        print("✅ Razorpay Order Created:", created_order)
        
        return JSONResponse({
            "success": True,
            "order_id": created_order["id"],
            "amount": created_order["amount"],
            "currency": created_order["currency"]
        })
    except Exception as e:
        print(f"❌ Error creating order: {str(e)}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

class VerifyPaymentRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str
    amount: float
    userid: int
    bill_id: str
    bill_type: str

class UpdateBillRequest(BaseModel):
    bill_id: str
    status: str

@app.post("/api/verify_payment/")
async def verify_payment(payment: VerifyPaymentRequest):
    try:
        data = {
            "razorpay_payment_id": payment.razorpay_payment_id,
            "razorpay_order_id": payment.razorpay_order_id,
            "razorpay_signature": payment.razorpay_signature
        }
        
        # Verify the payment signature
        is_valid = razorpay_client.utility.verify_payment_signature(data)

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        if is_valid:
            print(f"✅ Payment verified for {payment.bill_type} bill ID: {payment.bill_id}")

            # Check if the bill_id starts with "WB" or "EB"
            if payment.bill_id.startswith("WB"):
                # Update water bill fields
                update_query = """
                    UPDATE billing
                    SET amount_water = 0, status_water = 'Paid'
                    WHERE water_id = %s;
                """
                cursor.execute(update_query, (payment.bill_id,))
                payment_type = "water"
            elif payment.bill_id.startswith("EB"):
                # Update electricity bill fields
                update_query = """
                    UPDATE billing
                    SET amount_current = 0, status_current = 'Paid'
                    WHERE current_id = %s;
                """
                cursor.execute(update_query, (payment.bill_id,))
                payment_type = "current"
            else:
                raise HTTPException(status_code=400, detail="❌ Invalid bill ID format.")

            # Insert a record into the payments table for a successful payment
            insert_payment_query = """
                INSERT INTO payments (pid, type, amount, payment_status, paid_at)
                VALUES (
                    (SELECT pid FROM billing WHERE water_id = %s OR current_id = %s),
                    %s,
                    %s,
                    'Success',
                    CURRENT_TIMESTAMP
                );
            """
            cursor.execute(insert_payment_query, (payment.bill_id, payment.bill_id, payment_type, payment.amount))

            # Commit the transaction and close the connection
            conn.commit()
            cursor.close()
            conn.close()

            return JSONResponse({
                "success": True,
                "message": "✅ Payment verified successfully. Bill updated."
            })

        else:
            # Insert a record into the payments table for a failed payment
            insert_payment_query = """
                INSERT INTO payments (pid, type, amount, payment_status, paid_at)
                VALUES (
                    (SELECT pid FROM billing WHERE water_id = %s OR current_id = %s),
                    %s,
                    %s,
                    'Failed',
                    CURRENT_TIMESTAMP
                );
            """
            cursor.execute(insert_payment_query, (payment.bill_id, payment.bill_id, payment.bill_type, payment.amount))

            # Commit the transaction and close the connection
            conn.commit()
            cursor.close()
            conn.close()

            raise HTTPException(status_code=400, detail="❌ Invalid payment signature.")

    except Exception as e:
        print(f"❌ Error verifying payment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error verifying payment: {str(e)}")
    try:
        data = {
            "razorpay_payment_id": payment.razorpay_payment_id,
            "razorpay_order_id": payment.razorpay_order_id,
            "razorpay_signature": payment.razorpay_signature
        }
        
        # Verify the payment signature
        is_valid = razorpay_client.utility.verify_payment_signature(data)

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        if is_valid:
            print(f"✅ Payment verified for {payment.bill_type} bill ID: {payment.bill_id}")

            # Check if the bill_id starts with "WB" or "EB"
            if payment.bill_id.startswith("WB"):
                # Update water bill fields
                update_query = """
                    UPDATE billing
                    SET amount_water = 0, status_water = 'Paid'
                    WHERE water_id = %s;
                """
                cursor.execute(update_query, (payment.bill_id,))
                payment_type = "water"
            elif payment.bill_id.startswith("EB"):
                # Update electricity bill fields
                update_query = """
                    UPDATE billing
                    SET amount_current = 0, status_current = 'Paid'
                    WHERE current_id = %s;
                """
                cursor.execute(update_query, (payment.bill_id,))
                payment_type = "current"
            else:
                raise HTTPException(status_code=400, detail="❌ Invalid bill ID format.")

            # Insert a record into the payments table for a successful payment
            insert_payment_query = """
                INSERT INTO payments (pid, type, amount, payment_status, paid_at)
                VALUES (
                    (SELECT pid FROM billing WHERE water_id = %s OR current_id = %s),
                    %s,
                    %s,
                    'Success',
                    CURRENT_TIMESTAMP
                );
            """
            cursor.execute(insert_payment_query, (payment.bill_id, payment.bill_id, payment.userid, payment_type, payment.amount))

            # Commit the transaction and close the connection
            conn.commit()
            cursor.close()
            conn.close()

            return JSONResponse({
                "success": True,
                "message": "✅ Payment verified successfully. Bill updated."
            })

        else:
            # Insert a record into the payments table for a failed payment
            insert_payment_query = """
                INSERT INTO payments (pid, type, amount, payment_status, paid_at)
                VALUES (
                    (SELECT pid FROM billing WHERE water_id = %s OR current_id = %s),
                    %s,
                    %s,
                    'Failed',
                    CURRENT_TIMESTAMP
                );
            """
            cursor.execute(insert_payment_query, (payment.bill_id, payment.bill_id, payment.userid, payment.bill_type, payment.amount))

            # Commit the transaction and close the connection
            conn.commit()
            cursor.close()
            conn.close()

            raise HTTPException(status_code=400, detail="❌ Invalid payment signature.")

    except Exception as e:
        print(f"❌ Error verifying payment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error verifying payment: {str(e)}")