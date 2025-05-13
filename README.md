# Utility Billing Management System

This project is a **Utility Billing Management System** designed for administrators to manage billing records, update billing dates, and send email notifications for unpaid bills. It also includes user-facing features for checking and paying bills.

---

## Features

### Admin Features:
- **Dashboard**: Overview of billing and user data.
- **Update Billing Date**: Update the billing date for all records in the database.
- **Send Due Emails**: Automatically send email reminders to users with unpaid bills.
- **Manage Users**: View and manage user details.
- **Generate Reports**: Generate billing and payment reports.

### User Features:
- **Check Bill Status**: Users can check the status of their water and electricity bills.
- **Pay Bills**: Users can pay their bills online using dynamically generated payment links.

---

## Project Structure

e:\projects\Santosh\socital_santhosh
ª   .env
ª   database.py
ª   main.py
ª   payment.py
ª   README.md
ª   requirements.txt
ª   route.py
ª
+---static
ª   +---images
ª           electricity.jpeg
ª           water.jpeg
ª
+---templates
ª   +---admin
ª   ª       bill_page.html
ª   ª       index.html
ª   ª       login.html
ª   ª       update_date.html
ª   ª       users.html
ª   ª
ª   +---external
ª   ª       billing.html
ª   ª
ª   +---users
ª           about.html
ª           billingstatus.html
ª           electricity_billing.html
ª           footer.html
ª           index.html
ª           nav.html
ª           pay.html
ª           paymenthistory.html
ª           register.html
ª           services.html
ª           water_billing.html

---

## Installation

### Prerequisites:
- Python 3.8 or higher (recomended Python 3.10.11)
- PostgreSQL
-fast API
pip install -r requirements.txt
### Steps:
1. Clone the repository:
   ```bash
   git clone https://github.com/crazyscriptright/utility-billing-system.git
   cd utility-billing-system

2. Install dependencies:
pip install -r requirements.txt

3. Set up the .env file: Create a .env file in the root directory and add the following:
RAZORPAY_KEY_ID="idsecret
RAZORPAY_KEY_SECRET=secread key from rozar pay;
DB_PASSWORD = "your-password"
DB_HOST = "localhost"
DB_PORT = "5432"
NEW_DB = "Utility" 
DB_USER = "use_name"
EMAIL_USER=your_email@example.com
EMAIL_PASSWORD=your_email_password

4. Run the application:
uvicorn main:app --reload

5. Open the application in your browser:
http://127.0.0.1:8000

## Default Credentials

### Admin Account:
- **Email**: admin@gmail.com
- **Password**: 123456

### External User Account:
- **Email**: external@gmail.com
- **Password**: 123456

> **Note**: Please change these default credentials after the first login for security purposes.


Contact
For any inquiries or support, please contact:

Name: Anil          
Email: Crazyscriptright@gmail.com

contribution
https://github.com/MubbassirKhan

License
This project is licensed under the MIT License. See the LICENSE file for details.

