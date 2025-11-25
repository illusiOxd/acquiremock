def payment_check(paymentId: str, db_payments: dict):
    if paymentId not in db_payments:
        return False, "Payment not found"
    payment = db_payments[paymentId]
    if payment["status"] == "paid" or payment["status"] == "complete":
        return False, "Payment already completed"

    return payment