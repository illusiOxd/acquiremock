import uuid
import httpx
import json

from fastapi.responses import RedirectResponse
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from models.invoice import CreateInvoiceResponse, CreateInvoiceRequest
from other.data import db_payments
from datetime import datetime
from other.miscFunctions import payment_check

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
        card_number: str = Form(...),
        expiry: str = Form(...),
        cvv: str = Form(...)
):
    payment = payment_check(payment_id, db_payments)

    if not isinstance(payment, dict):
        raise HTTPException(status_code=404, detail="Payment not found or already completed")

    card_number_clean = card_number.replace(" ", "")

    if card_number_clean == "4444444444444444":
        payment["status"] = "paid"
        payment["paid_at"] = datetime.now().isoformat()
        payment["card_mask"] = f"**** **** **** {card_number_clean[-4:]}"

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
                    print(f"Відправляю Webhook на: {webhook_url}")
                    try:
                        await client.post(webhook_url, json=webhook_data)
                    except Exception as e:
                        print(f"Failed to send webhook request: {e}")
                else:
                    print("Webhook URL відсутній.")

        except Exception as e:
            print(f"Помилка при ініціалізації клієнта: {e}")

        return RedirectResponse(
            url=f"/success/{payment_id}",
            status_code=303
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Insufficient funds"
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