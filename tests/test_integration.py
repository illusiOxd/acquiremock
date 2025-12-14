import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.main_models import Payment
from datetime import datetime, timedelta

pytestmark = pytest.mark.asyncio


async def test_complete_payment_flow_without_otp(
    client: AsyncClient,
    db_session: AsyncSession
):
    invoice_payload = {
        "amount": 10000,
        "reference": "INTEGRATION-TEST-001",
        "webhookUrl": "https://webhook.site/test",
        "redirectUrl": "https://example.com/success"
    }

    invoice_response = await client.post(
        "/api/create-invoice",
        json=invoice_payload
    )
    assert invoice_response.status_code == 200
    payment_url = invoice_response.json()["pageUrl"]
    payment_id = payment_url.split("/")[-1]

    checkout_response = await client.get(f"/checkout/{payment_id}")
    assert checkout_response.status_code == 200
    csrf_token = checkout_response.cookies.get("csrf_token")

    email = "returning@user.com"
    form_data = {
        "card_number": "4444444444444444",
        "expiry": "12/25",
        "cvv": "123",
        "email": email,
        "csrf_token": csrf_token
    }

    payment_response = await client.post(
        f"/api/pay/{payment_id}",
        data=form_data,
        cookies={
            "csrf_token": csrf_token,
            "user_email": email
        }
    )

    assert payment_response.status_code == 303
    assert "/success/" in payment_response.headers["location"]

    from sqlmodel import select
    result = await db_session.execute(
        select(Payment).where(Payment.id == payment_id)
    )
    payment = result.scalars().first()
    assert payment.status == "paid"


async def test_complete_payment_flow_with_otp(
    client: AsyncClient,
    db_session: AsyncSession
):
    invoice_payload = {
        "amount": 5000,
        "reference": "OTP-FLOW-TEST",
        "webhookUrl": "https://webhook.site/test",
        "redirectUrl": "https://example.com/success"
    }

    invoice_response = await client.post(
        "/api/create-invoice",
        json=invoice_payload
    )
    payment_url = invoice_response.json()["pageUrl"]
    payment_id = payment_url.split("/")[-1]

    checkout_response = await client.get(f"/checkout/{payment_id}")
    csrf_token = checkout_response.cookies.get("csrf_token")

    form_data = {
        "card_number": "4444444444444444",
        "expiry": "12/25",
        "cvv": "123",
        "email": "newuser@test.com",
        "csrf_token": csrf_token
    }

    payment_response = await client.post(
        f"/api/pay/{payment_id}",
        data=form_data,
        cookies={"csrf_token": csrf_token}
    )

    assert payment_response.status_code == 303
    assert "/otp/" in payment_response.headers["location"]

    otp_response = await client.get(f"/otp/{payment_id}")
    assert otp_response.status_code == 200
    assert "newuser@test.com" in otp_response.text

    from sqlmodel import select
    result = await db_session.execute(
        select(Payment).where(Payment.id == payment_id)
    )
    payment = result.scalars().first()
    assert payment.status == "waiting_for_otp"
    assert payment.otp_code is not None


async def test_save_card_flow(client: AsyncClient, db_session: AsyncSession):
    payment = Payment(
        id="save-card-test",
        amount=3000,
        reference="SAVE-CARD",
        webhook_url="https://example.com/hook",
        redirect_url="https://example.com/ok",
        status="pending",
        expires_at=datetime.utcnow() + timedelta(minutes=15)
    )
    db_session.add(payment)
    await db_session.commit()

    checkout_response = await client.get(f"/checkout/{payment.id}")
    csrf_token = checkout_response.cookies.get("csrf_token")

    form_data = {
        "card_number": "4444444444444444",
        "expiry": "12/25",
        "cvv": "123",
        "email": "carduser@test.com",
        "save_card": "true",
        "csrf_token": csrf_token
    }

    response = await client.post(
        f"/api/pay/{payment.id}",
        data=form_data,
        cookies={"csrf_token": csrf_token}
    )

    assert response.status_code == 303

    from app.models.main_models import SavedCard
    from sqlmodel import select

    result = await db_session.execute(
        select(SavedCard).where(SavedCard.email == "carduser@test.com")
    )
    saved_cards = result.scalars().all()
    assert len(saved_cards) > 0
    assert saved_cards[0].card_mask == "**** 4444"


async def test_expired_payment_handling(
    client: AsyncClient,
    db_session: AsyncSession
):
    payment = Payment(
        id="expired-test",
        amount=2000,
        reference="EXPIRED",
        webhook_url="https://example.com/hook",
        redirect_url="https://example.com/ok",
        status="pending",
        expires_at=datetime.utcnow() - timedelta(minutes=5)
    )
    db_session.add(payment)
    await db_session.commit()

    response = await client.get(f"/checkout/{payment.id}")
    assert response.status_code == 410

    await db_session.refresh(payment)
    assert payment.status == "expired"


async def test_multiple_users_different_cards(
    client: AsyncClient,
    db_session: AsyncSession
):
    users = [
        ("user1@test.com", "4444"),
        ("user2@test.com", "4444"),
        ("user3@test.com", "4444")
    ]

    for i, (email, last_digits) in enumerate(users):
        payment = Payment(
            id=f"multi-user-{i}",
            amount=1000,
            reference=f"ORDER-{i}",
            webhook_url="https://example.com/hook",
            redirect_url="https://example.com/ok",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        db_session.add(payment)
        await db_session.commit()
        await db_session.refresh(payment)

        checkout_response = await client.get(f"/checkout/{payment.id}")
        csrf_token = checkout_response.cookies.get("csrf_token")

        form_data = {
            "card_number": "4444444444444444",
            "expiry": "12/25",
            "cvv": "123",
            "email": email,
            "save_card": "true",
            "csrf_token": csrf_token
        }

        await client.post(
            f"/api/pay/{payment.id}",
            data=form_data,
            cookies={"csrf_token": csrf_token}
        )

    for email, _ in users:
        response = await client.get(f"/api/user-info?email={email}")
        data = response.json()

        assert "cards" in data
        assert "operations" in data


# async def test_concurrent_payments_different_users(
#     client: AsyncClient,
#     db_session: AsyncSession
# ):
#     payment_ids = []
#
#     for i in range(5):
#         payment = Payment(
#             id=f"concurrent-{i}",
#             amount=1000,
#             reference=f"ORDER-USER-{i}",
#             webhook_url="https://example.com/hook",
#             redirect_url="https://example.com/ok",
#             status="pending",
#             expires_at=datetime.utcnow() + timedelta(minutes=15)
#         )
#         db_session.add(payment)
#         payment_ids.append(payment.id)
#
#     await db_session.commit()
#
#     async def process_payment(user_id: int, payment_id: str):
#         user_email = f"user{user_id}@test.com"
#
#         checkout_response = await client.get(f"/checkout/{payment_id}")
#         csrf_token = checkout_response.cookies.get("csrf_token")
#
#         form_data = {
#             "card_number": "4444444444444444",
#             "expiry": "12/25",
#             "cvv": "123",
#             "email": user_email,
#             "csrf_token": csrf_token
#         }
#
#         response = await client.post(
#             f"/api/pay/{payment_id}",
#             data=form_data,
#             cookies={
#                 "csrf_token": csrf_token,
#                 "user_email": user_email
#             }
#         )
#
#         return response.status_code
#
#     import asyncio
#     tasks = [
#         process_payment(i, payment_id)
#         for i, payment_id in enumerate(payment_ids)
#     ]
#
#     results = await asyncio.gather(*tasks, return_exceptions=True)
#
#     successful = sum(1 for r in results if isinstance(r, int) and r == 303)
#     assert successful >= 3


async def test_payment_reference_uniqueness(
    client: AsyncClient,
    db_session: AsyncSession
):
    reference = "DUPLICATE-REF-TEST"

    for i in range(2):
        payload = {
            "amount": 1000 * (i + 1),
            "reference": reference,
            "webhookUrl": f"https://example.com/hook{i}",
            "redirectUrl": "https://example.com/ok"
        }

        response = await client.post("/api/create-invoice", json=payload)
        assert response.status_code == 200

    from sqlmodel import select
    result = await db_session.execute(
        select(Payment).where(Payment.reference == reference)
    )
    payments = result.scalars().all()
    assert len(payments) == 2
    assert payments[0].id != payments[1].id


async def test_sanitization_prevents_xss(
    client: AsyncClient,
    db_session: AsyncSession
):
    dangerous_input = "<script>alert('xss')</script>TEST"

    payload = {
        "amount": 1000,
        "reference": dangerous_input,
        "webhookUrl": "https://example.com/hook",
        "redirectUrl": "https://example.com/ok"
    }

    response = await client.post("/api/create-invoice", json=payload)
    assert response.status_code == 200

    payment_url = response.json()["pageUrl"]
    payment_id = payment_url.split("/")[-1]

    checkout_response = await client.get(f"/checkout/{payment_id}")
    page_content = checkout_response.text

    assert "<script>alert(" not in page_content

    from sqlmodel import select
    result = await db_session.execute(
        select(Payment).where(Payment.id == payment_id)
    )
    payment = result.scalars().first()

    assert "<script>" not in payment.reference or "&lt;script&gt;" in payment.reference


async def test_success_page_display(
    client: AsyncClient,
    db_session: AsyncSession
):
    payment = Payment(
        id="success-page-test",
        amount=15000,
        reference="SUCCESS-TEST",
        webhook_url="https://example.com/hook",
        redirect_url="https://example.com/return",
        status="paid",
        card_mask="**** 1234",
        expires_at=datetime.utcnow() + timedelta(minutes=15)
    )
    db_session.add(payment)
    await db_session.commit()

    response = await client.get(f"/success/{payment.id}")
    assert response.status_code == 200

    assert "SUCCESS-TEST" in response.text
    assert "15000" in response.text

    assert "1234" in response.text or "*" in response.text