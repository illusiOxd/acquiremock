import uuid
import httpx
import json

from fastapi.responses import RedirectResponse
from fastapi import FastAPI, HTTPException, Request, Form, BackgroundTasks
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from models.invoice import CreateInvoiceResponse, CreateInvoiceRequest
from other.data import db_payments
from datetime import datetime
from other.miscFunctions import payment_check, generate_otp, validate_otp
from services.smtp_service import send_otp_email

app = FastAPI(
    title="AcquireMock",
    description="AcquireMock is a microservice for Feane Project.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def read_root():
    return {
        "service": "AcquireMock Payment Gateway",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "create_invoice": "POST /api/create-invoice",
            "checkout": "GET /checkout/{payment_id}",
            "process_payment": "POST /pay/{payment_id}",
            "verify_otp": "POST /otp/verify/{payment_id}",
            "success": "GET /success/{payment_id}",
            "health": "GET /health"
        }
    }


@app.post("/api/create-invoice", response_model=CreateInvoiceResponse)
async def create_invoice(invoice: CreateInvoiceRequest):
    payment_id = str(uuid.uuid4())

    db_payments[payment_id] = {
        "amount": invoice.amount,
        "reference": invoice.reference,
        "webhook_url": invoice.webhook_url,
        "redirect_url": invoice.redirect_url,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }

    page_url = f"http://localhost:8002/checkout/{payment_id}"
    return CreateInvoiceResponse(pageUrl=page_url)


@app.get("/checkout/{payment_id}")
async def checkout(payment_id: str, request: Request):
    payment = payment_check(payment_id, db_payments)

    if not isinstance(payment, dict):
        raise HTTPException(status_code=404, detail="Payment not found or already completed")

    return templates.TemplateResponse(
        "checkout.html",
        {
            "request": request,
            "payment_id": payment_id,
            "amount": payment["amount"],
            "reference": payment["reference"]
        }
    )


@app.post("/pay/{payment_id}")
async def process_payment(
        payment_id: str,
        background_tasks: BackgroundTasks,
        card_number: str = Form(...),
        expiry: str = Form(...),
        cvv: str = Form(...),
        email: str = Form(...)
):
    payment = payment_check(payment_id, db_payments)

    if not isinstance(payment, dict):
        raise HTTPException(status_code=404, detail="Payment not found or already completed")

    card_number_clean = card_number.replace(" ", "")

    if card_number_clean == "4444444444444444":
        otp_code = generate_otp()

        user_email = email

        payment.update({
            "otp_code": otp_code,
            "otp_email": user_email,
            "card_mask": f"**** **** **** {card_number_clean[-4:]}",
            "status": "waiting_for_otp"
        })

        background_tasks.add_task(send_otp_email, user_email, otp_code)

        return RedirectResponse(
            url=f"/otp/{payment_id}",
            status_code=303
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Insufficient funds"
        )


@app.get("/otp/{payment_id}")
async def otp_page(payment_id: str, request: Request):
    payment = payment_check(payment_id, db_payments)

    if not isinstance(payment, dict):
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.get("status") != "waiting_for_otp":
        raise HTTPException(status_code=400, detail="Invalid payment state")

    user_email = payment.get("otp_email", "unknown")
    masked_email = user_email

    return templates.TemplateResponse(
        "otp-page.html",
        {
            "request": request,
            "payment_id": payment_id,
            "email": masked_email
        }
    )


@app.post("/otp/verify/{payment_id}")
async def verify_otp(payment_id: str, otp_code: str = Form(...)):
    payment = payment_check(payment_id, db_payments)

    if not isinstance(payment, dict):
        raise HTTPException(status_code=404, detail="Payment not found")

    if not validate_otp(payment, otp_code):
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    payment["status"] = "paid"
    payment["paid_at"] = datetime.now().isoformat()
    payment["otp_code"] = None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            webhook_data = {
                "payment_id": payment_id,
                "reference": payment["reference"],
                "amount": payment["amount"],
                "status": "success",
                "paid_at": payment["paid_at"]
            }
            webhook_url = payment.get("webhook_url")
            if webhook_url:
                print(f"Sending Webhook to: {webhook_url}")
                try:
                    await client.post(webhook_url, json=webhook_data)
                except Exception as e:
                    print(f"Failed to send webhook request: {e}")
            else:
                print("Webhook URL missing.")

    except Exception as e:
        print(f"Error initializing client: {e}")

    return RedirectResponse(
        url=f"/success/{payment_id}",
        status_code=303
    )


@app.get("/success/{payment_id}")
async def payment_success(payment_id: str, request: Request):
    if payment_id not in db_payments:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment = db_payments[payment_id]

    return templates.TemplateResponse(
        "success-page.html",
        {
            "request": request,
            "payment_id": payment_id,
            "amount": payment["amount"],
            "reference": payment["reference"],
            "card_mask": payment.get("card_mask", "**** **** **** ****"),
            "redirect_url": payment.get("redirect_url", "/")
        }
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8002, reload=True)