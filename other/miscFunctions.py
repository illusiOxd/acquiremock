import random


def payment_check(paymentId: str, db_payments: dict):
    if paymentId not in db_payments:
        return False, "Payment not found"
    payment = db_payments[paymentId]
    if payment["status"] == "paid" or payment["status"] == "complete":
        return False, "Payment already completed"

    return payment


def generate_otp() -> str:
    """Generates a random 4-digit OTP code."""
    return str(random.randint(1000, 9999))


def validate_otp(payment: dict, input_code: str) -> bool:
    """
    Validates the input OTP code against the stored code in the payment object.
    Returns True if valid, False otherwise.
    """
    stored_code = payment.get("otp_code")

    if not stored_code:
        return False

    if input_code != stored_code:
        return False

    return True