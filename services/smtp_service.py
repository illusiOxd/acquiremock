import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')


def send_otp_email(to_email, otp_code):
    subject = "AcquireMock: Ваш код підтвердження"

    template_path = Path("templates/misc/email-letter.html")

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"Помилка: Файл шаблону {template_path} не знайдено.")
        html_content = f"<h1>Code: {otp_code}</h1>"

    html_body = html_content.replace("{{ code }}", str(otp_code))

    msg = MIMEMultipart("alternative")
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email

    text_body = f"Ваш код підтвердження: {otp_code}"

    part1 = MIMEText(text_body, "plain", "utf-8")
    part2 = MIMEText(html_body, "html", "utf-8")

    msg.attach(part1)
    msg.attach(part2)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [to_email], msg.as_string())
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")


if __name__ == "__main__":
    send_otp_email("test@example.com", "1234")