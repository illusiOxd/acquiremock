import pytest
from app.security.crypto import (
    generate_secure_otp,
    generate_csrf_token,
    hash_sensitive_data,
    verify_sensitive_data
)
from app.security.sanitizer import clean_input
from app.services.webhook_service import (
    generate_webhook_signature,
    verify_webhook_signature
)


def test_generate_secure_otp():
    otp = generate_secure_otp()
    assert len(otp) == 4
    assert otp.isdigit()

    otp_long = generate_secure_otp(6)
    assert len(otp_long) == 6
    assert otp_long.isdigit()


def test_generate_secure_otp_uniqueness():
    otps = [generate_secure_otp() for _ in range(100)]
    assert len(set(otps)) > 80


def test_generate_csrf_token():
    token1 = generate_csrf_token()
    token2 = generate_csrf_token()

    assert len(token1) > 20
    assert len(token2) > 20

    assert token1 != token2


def test_hash_sensitive_data():
    data = "4444444444444444"
    hashed = hash_sensitive_data(data)

    assert hashed != data
    assert len(hashed) > len(data)

    assert hashed.startswith("$2b$")


def test_verify_sensitive_data():
    original = "4444444444444444"
    hashed = hash_sensitive_data(original)

    assert verify_sensitive_data(original, hashed) is True

    assert verify_sensitive_data("1111111111111111", hashed) is False


def test_hash_is_consistent():
    data = "test_data"
    hash1 = hash_sensitive_data(data)
    hash2 = hash_sensitive_data(data)

    assert hash1 != hash2

    assert verify_sensitive_data(data, hash1) is True
    assert verify_sensitive_data(data, hash2) is True


def test_clean_input_removes_xss():
    dangerous = "<script>alert('xss')</script>"
    cleaned = clean_input(dangerous)

    assert "<script>" not in cleaned
    assert "alert" in cleaned


def test_clean_input_removes_javascript():
    dangerous = "javascript:alert('xss')"
    cleaned = clean_input(dangerous)

    assert "javascript:" not in cleaned.lower()


def test_clean_input_escapes_html():
    dangerous = '<img src="x" onerror="alert(1)">'
    cleaned = clean_input(dangerous)

    assert "&lt;" in cleaned or "<img" not in cleaned


def test_clean_input_preserves_safe_text():
    safe_text = "Order #12345 - Customer Name"
    cleaned = clean_input(safe_text)

    assert cleaned == safe_text


def test_clean_input_handles_empty_string():
    assert clean_input("") == ""
    assert clean_input(None) == ""


def test_clean_input_strips_whitespace():
    text = "  test data  "
    cleaned = clean_input(text)

    assert cleaned == "test data"


def test_clean_input_complex_xss():
    attacks = [
        "');alert('xss');//",
        "<iframe src='javascript:alert(1)'>",
        "<<SCRIPT>alert('XSS');//<</SCRIPT>",
        "<IMG SRC=j&#X41vascript:alert('test')>",
    ]

    for attack in attacks:
        cleaned = clean_input(attack)
        assert "javascript:" not in cleaned.lower()
        assert "<script" not in cleaned.lower()


def test_generate_webhook_signature():
    payload = {
        "payment_id": "test-123",
        "amount": 5000,
        "status": "paid"
    }

    secret = "test_secret"
    signature = generate_webhook_signature(payload, secret)

    assert len(signature) == 64
    assert all(c in "0123456789abcdef" for c in signature)


def test_webhook_signature_is_deterministic():
    payload = {
        "payment_id": "test-123",
        "amount": 5000,
        "status": "paid"
    }

    secret = "test_secret"
    sig1 = generate_webhook_signature(payload, secret)
    sig2 = generate_webhook_signature(payload, secret)

    assert sig1 == sig2


def test_webhook_signature_key_order_independent():
    payload1 = {
        "payment_id": "test-123",
        "amount": 5000,
        "status": "paid"
    }

    payload2 = {
        "status": "paid",
        "payment_id": "test-123",
        "amount": 5000
    }

    secret = "test_secret"
    sig1 = generate_webhook_signature(payload1, secret)
    sig2 = generate_webhook_signature(payload2, secret)

    assert sig1 == sig2


def test_webhook_signature_different_data():
    secret = "test_secret"

    payload1 = {"payment_id": "test-123", "amount": 5000}
    payload2 = {"payment_id": "test-123", "amount": 6000}

    sig1 = generate_webhook_signature(payload1, secret)
    sig2 = generate_webhook_signature(payload2, secret)

    assert sig1 != sig2


def test_webhook_signature_different_secret():
    payload = {"payment_id": "test-123", "amount": 5000}

    sig1 = generate_webhook_signature(payload, "secret1")
    sig2 = generate_webhook_signature(payload, "secret2")

    assert sig1 != sig2


def test_verify_webhook_signature_valid():
    payload = {
        "payment_id": "test-123",
        "amount": 5000,
        "status": "paid"
    }

    secret = "test_secret"
    signature = generate_webhook_signature(payload, secret)

    assert verify_webhook_signature(payload, signature, secret) is True


def test_verify_webhook_signature_invalid():
    payload = {
        "payment_id": "test-123",
        "amount": 5000,
        "status": "paid"
    }

    secret = "test_secret"
    wrong_signature = "0" * 64

    assert verify_webhook_signature(payload, wrong_signature, secret) is False


def test_verify_webhook_signature_modified_payload():
    payload = {
        "payment_id": "test-123",
        "amount": 5000,
        "status": "paid"
    }

    secret = "test_secret"
    signature = generate_webhook_signature(payload, secret)

    payload["amount"] = 6000

    assert verify_webhook_signature(payload, signature, secret) is False


def test_verify_webhook_signature_wrong_secret():
    payload = {
        "payment_id": "test-123",
        "amount": 5000,
        "status": "paid"
    }

    signature = generate_webhook_signature(payload, "secret1")

    assert verify_webhook_signature(payload, signature, "secret2") is False


def test_payment_status_transitions():
    from app.models.main_models import PaymentStatus

    assert PaymentStatus.PENDING == "pending"
    assert PaymentStatus.WAITING_FOR_OTP == "waiting_for_otp"
    assert PaymentStatus.PAID == "paid"
    assert PaymentStatus.FAILED == "failed"
    assert PaymentStatus.EXPIRED == "expired"
    assert PaymentStatus.REFUNDED == "refunded"


def test_payment_model_defaults():
    from app.models.main_models import Payment
    from datetime import datetime, timedelta

    payment = Payment(
        id="test-defaults",
        amount=1000,
        reference="TEST",
        webhook_url="https://example.com",
        redirect_url="https://example.com"
    )

    assert payment.status == "pending"
    assert payment.webhook_attempts == 0
    assert payment.otp_code is None
    assert payment.otp_email is None

    assert isinstance(payment.created_at, datetime)
    assert isinstance(payment.updated_at, datetime)
    assert isinstance(payment.expires_at, datetime)

    time_diff = payment.expires_at - payment.created_at
    assert 14 <= time_diff.total_seconds() / 60 <= 16


def test_saved_card_model():
    from app.models.main_models import SavedCard
    from datetime import datetime

    card = SavedCard(
        email="test@example.com",
        card_token="token_123",
        card_hash="hash_123",
        cvv_hash="cvv_hash",
        expiry="12/25",
        card_mask="**** 4444",
        psp_provider="mock"
    )

    assert card.email == "test@example.com"
    assert card.psp_provider == "mock"
    assert isinstance(card.created_at, datetime)


def test_webhook_log_model():
    from app.models.main_models import WebhookLog

    log = WebhookLog(
        payment_id="test-123",
        webhook_url="https://example.com/hook",
        payload='{"test": "data"}',
        signature="abc123",
        attempt_number=1,
        success=True
    )

    assert log.payment_id == "test-123"
    assert log.success is True
    assert log.attempt_number == 1


def test_successful_operation_model():
    from app.models.main_models import SuccessfulOperation

    op = SuccessfulOperation(
        payment_id="test-123",
        email="user@test.com",
        amount=5000,
        reference="ORDER-123",
        card_mask="**** 4444",
        redirect_url="https://example.com"
    )

    assert op.payment_id == "test-123"
    assert op.email == "user@test.com"
    assert op.amount == 5000


def test_payment_error_models():
    from app.models.errors import (
        PaymentNotFoundError,
        PaymentAlreadyProcessedError,
        PaymentExpiredError,
        InsufficientFundsError,
        InvalidOTPError,
        CSRFTokenMismatchError
    )

    error = PaymentNotFoundError("test-123")
    assert error.code == "PAYMENT_NOT_FOUND"
    assert error.status_code == 404
    assert error.payment_id == "test-123"

    error = PaymentAlreadyProcessedError("test-456")
    assert error.code == "PAYMENT_ALREADY_PROCESSED"
    assert error.status_code == 409

    error = PaymentExpiredError("test-789")
    assert error.code == "PAYMENT_EXPIRED"
    assert error.status_code == 410

    error = InsufficientFundsError()
    assert error.code == "INSUFFICIENT_FUNDS"
    assert error.status_code == 402

    error = InvalidOTPError("test-otp")
    assert error.code == "INVALID_OTP"
    assert error.status_code == 401

    error = CSRFTokenMismatchError()
    assert error.code == "CSRF_TOKEN_MISMATCH"
    assert error.status_code == 403


def test_invoice_request_model():
    from app.models.invoice import CreateInvoiceRequest

    request = CreateInvoiceRequest(
        amount=5000,
        reference="TEST-123",
        webhookUrl="https://example.com/hook",
        redirectUrl="https://example.com/success"
    )

    assert request.amount == 5000
    assert request.reference == "TEST-123"

    data = {
        "amount": 10000,
        "reference": "TEST",
        "webhookUrl": "https://test.com",
        "redirectUrl": "https://test.com"
    }
    request = CreateInvoiceRequest(**data)
    assert request.webhook_url == "https://test.com"


def test_config_loading():
    from app.core.config import (
        BASE_URL,
        CURRENCY_CODE,
        CURRENCY_SYMBOL,
        WEBHOOK_SECRET
    )

    assert BASE_URL is not None
    assert CURRENCY_CODE is not None
    assert CURRENCY_SYMBOL is not None
    assert WEBHOOK_SECRET is not None

    assert isinstance(BASE_URL, str)
    assert isinstance(CURRENCY_CODE, str)
    assert isinstance(CURRENCY_SYMBOL, str)
    assert isinstance(WEBHOOK_SECRET, str)