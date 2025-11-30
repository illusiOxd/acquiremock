# AcquireMock Payment Gateway v2.0

Mock payment gateway для тестування інтеграції з платіжними системами.

## Нові можливості v2.0

- ✅ Зберігання платежів в БД (PostgreSQL/SQLite)
- ✅ Webhook з підписом (HMAC-SHA256)
- ✅ Retry механізм для webhooks
- ✅ Idempotency keys
- ✅ Автоматичне закінчення платежів (TTL 15 хв)
- ✅ Background tasks для обробки
- ✅ Structured error handling
- ✅ Webhook verification endpoint

## Встановлення

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

pip install -r requirements.txt

cp .env.example .env
```

## Налаштування .env

```env
DATABASE_URL=sqlite+aiosqlite:///./payment.db
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
WEBHOOK_SECRET=your-secret-key-min-32-chars
```

## Запуск

```bash
uvicorn main:app --port 8002 --reload
```

## API Endpoints

### POST /api/create-invoice
Створення нового платежу

**Request:**
```json
{
  "amount": 25000,
  "reference": "ORDER-123",
  "webhook_url": "https://your-site.com/webhook",
  "redirect_url": "https://your-site.com/success"
}
```

**Response:**
```json
{
  "pageUrl": "http://localhost:8002/checkout/{payment_id}"
}
```

### POST /webhooks/verify
Перевірка підпису webhook

**Headers:**
```
X-Signature: hmac-sha256-signature
```

**Request:**
```json
{
  "payment_id": "uuid",
  "reference": "ORDER-123",
  "amount": 25000,
  "status": "paid"
}
```

## Webhook Integration

### Отримання webhook в Django

```python
import hmac
import hashlib
import json

def verify_webhook_signature(payload: dict, signature: str, secret: str) -> bool:
    message = json.dumps(payload, sort_keys=True)
    expected = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@csrf_exempt
def payment_webhook(request):
    if request.method == 'POST':
        signature = request.headers.get('X-Signature')
        payload = json.loads(request.body)
        
        if not verify_webhook_signature(payload, signature, settings.WEBHOOK_SECRET):
            return JsonResponse({'error': 'Invalid signature'}, status=403)
        
        payment_id = payload['payment_id']
        status = payload['status']
        
        if status == 'paid':
            order = Order.objects.get(payment_id=payment_id)
            order.status = 'paid'
            order.save()
        
        return JsonResponse({'status': 'ok'})
```

## Тестові дані

- **Успішна картка:** 4444 4444 4444 4444
- **CVV:** будь-який
- **Термін:** будь-який (MM/YY)

## Структура БД

### Таблиця `payments`
- id (UUID, PK)
- amount (float)
- reference (string, indexed)
- status (enum: pending/waiting_for_otp/paid/failed/expired)
- webhook_url (string)
- webhook_attempts (int)
- webhook_status (string)
- idempotency_key (string, indexed)
- expires_at (datetime)
- created_at, updated_at, paid_at

### Таблиця `webhook_logs`
- payment_id (FK)
- webhook_url
- payload (JSON)
- response_status
- signature
- attempt_number
- success (bool)

## Background Tasks

1. **expire_pending_payments_task** - закінчує платежі старше 15 хвилин (кожну хвилину)
2. **retry_failed_webhooks_task** - повторює failed webhooks до 5 спроб (кожні 5 хвилин)

## Production Checklist

- [ ] Замінити SQLite на PostgreSQL
- [ ] Налаштувати WEBHOOK_SECRET (32+ символів)
- [ ] Додати rate limiting per user
- [ ] Налаштувати Sentry/logging
- [ ] Додати моніторинг (Prometheus/Grafana)
- [ ] SSL certificates
- [ ] Firewall rules
- [ ] Backup strategy для БД

## Міграція на реальний PSP

Для переходу на Fondy/Stripe:
1. Замінити валідацію картки на API виклик PSP
2. Використовувати токенізацію замість зберігання карток
3. Реалізувати 3D Secure flow
4. Додати refund endpoint

## License

MIT