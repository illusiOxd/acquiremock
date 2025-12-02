import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import resend

load_dotenv()

logger = logging.getLogger(__name__)

resend.api_key = os.getenv('RESEND_API_KEY')
RESEND_FROM_EMAIL = os.getenv('RESEND_FROM_EMAIL', 'AcquireMock <onboarding@resend.dev>')


async def send_email(to_email, subject, html_content, text_content):
    logger.info(f"Preparing to send email to {to_email} with subject: {subject}")

    try:
        params = {
            "from": RESEND_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }

        email = resend.Emails.send(params)
        logger.info(f"Email successfully sent to {to_email}. ID: {email.get('id')}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}. Error: {e}", exc_info=True)


async def send_otp_email(to_email, otp_code):
    subject = "AcquireMock: Ваш код підтвердження"
    base_dir = Path(__file__).resolve().parent.parent
    template_path = base_dir / "templates" / "misc" / "email-letter.html"

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        logger.warning(f"Template file not found at {template_path}. Using fallback content.")
        html_content = f"<h1>Code: {otp_code}</h1>"

    html_body = html_content.replace("{{ code }}", str(otp_code))
    text_body = f"Ваш код підтвердження: {otp_code}"

    await send_email(to_email, subject, html_body, text_body)


async def send_receipt_email(to_email, payment_data):
    subject = f"Чек про оплату замовлення #{payment_data.get('reference')}"
    base_dir = Path(__file__).resolve().parent.parent
    template_path = base_dir / "templates" / "misc" / "receipt.html"

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        logger.warning(f"Template file not found at {template_path}. Using fallback content.")
        html_content = "<h1>Payment Successful</h1>"

    replacements = {
        "{{ amount }}": str(payment_data.get('amount')),
        "{{ reference }}": str(payment_data.get('reference')),
        "{{ date }}": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "{{ card_mask }}": payment_data.get('card_mask', '****'),
        "{{ payment_id }}": payment_data.get('payment_id', '')
    }

    for key, value in replacements.items():
        html_content = html_content.replace(key, value)

    text_body = f"Оплата успішна. Сума: {payment_data.get('amount')} грн. Замовлення: {payment_data.get('reference')}"

    await send_email(to_email, subject, html_content, text_body)


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)