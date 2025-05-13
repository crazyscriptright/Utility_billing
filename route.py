from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
import psycopg2
from passlib.context import CryptContext
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from database import *
from fastapi.templating import Jinja2Templates
import uuid
from datetime import datetime, timedelta
from datetime import date
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import Request, Query
from starlette.responses import RedirectResponse

templates = Jinja2Templates(directory="templates")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
# Add session middleware (change secret_key for production)
app.add_middleware(SessionMiddleware, secret_key="supersecretkey", session_cookie="session_id")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user_name = request.session.get("user_name", "Guest") 
    # Default to 'Guest' if not logged in
    print("Active User : ", user_name)
    return templates.TemplateResponse("users/index.html", {"request": request, "user_name": user_name})



@app.get("/register", response_class=HTMLResponse)
def register(request: Request):
    user_name = request.session.get("user_name", "Guest") 

    return templates.TemplateResponse("users/register.html", {"request": request, "user_name": user_name})

@app.get("/services", response_class=HTMLResponse)
def services(request: Request):
    user_name = request.session.get("user_name", "Guest") 

    return templates.TemplateResponse("users/services.html", {"request": request, "user_name": user_name})

@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    user_name = request.session.get("user_name", "Guest") 

    return templates.TemplateResponse("users/about.html", {"request": request, "user_name": user_name})

@app.get("/water_billing", response_class=HTMLResponse)
def water_billing(request: Request):
    user_name = request.session.get("user_name", "Guest") 

    return templates.TemplateResponse("users/water_billing.html", {"request": request, "user_name": user_name})

@app.get("/electricity_billing", response_class=HTMLResponse)
def electricity_billing(request: Request):
    user_name = request.session.get("user_name", "Guest") 

    return templates.TemplateResponse("users/electricity_billing.html", {"request": request, "user_name": user_name})



@app.get("/billingstatus", response_class=HTMLResponse)
def billingstatus(request: Request):
    user_name = request.session.get("user_name", "Guest") 

    return templates.TemplateResponse("users/billingstatus.html", {"request": request, "user_name": user_name})

@app.get("/paymenthistory", response_class=HTMLResponse)
def paymenthistory(request: Request):
    user_name = request.session.get("user_name", "Guest") 

    return templates.TemplateResponse("users/paymenthistory.html", {"request": request, "user_name": user_name})


@app.get("/pay", response_class=HTMLResponse)
def pay(
    request: Request, 
    bill_id: str = Query(None),  
    bill_type: str = Query(None), 
    current_id: str = Query(None)  # Allow `current_id` as an alternative to `bill_id`
):
    # Use `current_id` if `bill_id` is missing
    bill_id = bill_id or current_id  

    if not bill_id or not bill_type:
        return HTMLResponse(content="<h3>Error: Missing bill_id or bill_type</h3>", status_code=400)

    return templates.TemplateResponse("users/pay.html", {
        "request": request,
        "bill_id": bill_id,
        "bill_type": bill_type
    })
###############################################Routings End Here#######################################################
######################################### ADMIN ROUTES ##########################################################

# Middleware to check admin access
def check_admin(request: Request):
    user_name = request.session.get("user_name")

    if not user_name:  # If no session, redirect to login
        return RedirectResponse(url="/register")

    if user_name != "Admin":  # If not admin, redirect to unauthorized
        return RedirectResponse(url="/unauthorized")

    return None  # If admin, proceed

@app.get("/admin/home", response_class=HTMLResponse)
def home(request: Request):
    response = check_admin(request)
    if response:
        return response  # Redirect if not admin

    return templates.TemplateResponse("admin/index.html", {"request": request})

@app.get("/admin/users_page", response_class=HTMLResponse)
def users(request: Request):
    response = check_admin(request)
    if response:
        return response  # Redirect if not admin

    return templates.TemplateResponse("admin/users.html", {"request": request})

@app.get("/admin/bill_page", response_class=HTMLResponse)
def bill(request: Request):
    response = check_admin(request)
    if response:
        return response  # Redirect if not admin

    return templates.TemplateResponse("admin/bill_page.html", {"request": request})

@app.get("/admin/update_date.html", response_class=HTMLResponse)
def update_date(request: Request):
    response = check_admin(request)
    if response:
        return response  # Redirect if not admin

    return templates.TemplateResponse("admin/update_date.html", {"request": request})
############################################## EXTERNAL ROUTES ##########################################################


@app.get("/external/billing", response_class=HTMLResponse)
def billing(request: Request):
    user_name = request.session.get("user_name")

    if not user_name:  # If user_name is missing, redirect to login
        return RedirectResponse(url="/register")

    if user_name != "External":  # If user is not "External", redirect to unauthorized
        return RedirectResponse(url="/unauthorized")

    print("Active User:", user_name)
    return templates.TemplateResponse("external/billing.html", {"request": request})
