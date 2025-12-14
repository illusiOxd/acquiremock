# AcquireMock Test Suite

Comprehensive test suite covering all aspects of the AcquireMock payment gateway.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_api_flow.py         # API endpoint tests
├── test_integration.py      # End-to-end integration tests
├── test_services.py         # Service and utility tests
└── test_payment.py          # Manual integration test (not run in CI)
```

## Running Tests

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx aiosqlite

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api_flow.py -v

# Run specific test
pytest tests/test_api_flow.py::test_create_invoice_success -v
```

### Environment Variables

Tests automatically set these variables:

```bash
TESTING=true
DATABASE_URL=sqlite+aiosqlite:///:memory:
WEBHOOK_SECRET=test_secret_key_for_testing_purposes_12345678
BASE_URL=http://test
```

## Test Coverage

### API Flow Tests (`test_api_flow.py`)

- ✅ Health check endpoint
- ✅ Root and test page loading
- ✅ Invoice creation (success & validation)
- ✅ XSS prevention in invoice creation
- ✅ Checkout page loading
- ✅ Expired payment handling
- ✅ Already paid payment rejection
- ✅ Payment with valid card
- ✅ Payment with invalid card
- ✅ CSRF protection
- ✅ Saved card payment
- ✅ User info retrieval
- ✅ Webhook signature verification
- ✅ Authentication flow
- ✅ Error handling (404, etc.)
- ✅ Rate limiting
- ✅ Idempotency

**Coverage: ~85%** of payment flow

### Integration Tests (`test_integration.py`)

- ✅ Complete payment flow without OTP
- ✅ Complete payment flow with OTP
- ✅ Save card during payment
- ✅ Expired payment handling
- ✅ Multiple users with different cards
- ✅ Concurrent payments
- ✅ Reference uniqueness
- ✅ XSS sanitization
- ✅ Success page display

**Coverage: ~90%** of end-to-end flows

### Service Tests (`test_services.py`)

- ✅ OTP generation and uniqueness
- ✅ CSRF token generation
- ✅ Data hashing and verification
- ✅ Input sanitization (XSS, JavaScript)
- ✅ Webhook signature generation/verification
- ✅ Model defaults and structure
- ✅ Error model validation
- ✅ Configuration loading

**Coverage: ~95%** of utilities

## Test Fixtures

### `db_session`

Provides isolated in-memory database for each test:

```python
async def test_example(db_session: AsyncSession):
    payment = Payment(...)
    db_session.add(payment)
    await db_session.commit()
```

### `client`

Provides HTTP test client:

```python
async def test_example(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
```

## Writing New Tests

### Basic Test Template

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio

async def test_my_feature(client: AsyncClient, db_session: AsyncSession):
    """Test description."""
    # Arrange
    # ... setup test data
    
    # Act
    response = await client.post("/api/endpoint", json={...})
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "expected_value"
```

### Testing with Database

```python
async def test_with_db(db_session: AsyncSession):
    """Test database operations."""
    from app.models.main_models import Payment
    from datetime import datetime, timedelta
    
    # Create test data
    payment = Payment(
        id="test-123",
        amount=5000,
        reference="TEST",
        webhook_url="https://test.com",
        redirect_url="https://test.com",
        status="pending",
        expires_at=datetime.utcnow() + timedelta(minutes=15)
    )
    
    db_session.add(payment)
    await db_session.commit()
    
    # Test operations
    from sqlmodel import select
    result = await db_session.execute(
        select(Payment).where(Payment.id == "test-123")
    )
    found_payment = result.scalars().first()
    
    assert found_payment is not None
    assert found_payment.amount == 5000
```

### Testing API Endpoints

```python
async def test_endpoint(client: AsyncClient):
    """Test API endpoint."""
    # POST request
    response = await client.post(
        "/api/create-invoice",
        json={
            "amount": 5000,
            "reference": "TEST",
            "webhookUrl": "https://test.com",
            "redirectUrl": "https://test.com"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "pageUrl" in data
    
    # GET request
    response = await client.get("/health")
    assert response.status_code == 200
```

## CI/CD Integration

Tests run automatically on:
- Push to `main` or `master`
- Pull requests to `main` or `master`

### GitHub Actions Workflow

```yaml
- name: Run tests
  run: pytest tests/ -v --tb=short --cov=app
```

### Test Timeout

All tests have a 30-second timeout to prevent hanging. This is enforced by:

1. pytest-timeout plugin
2. GitHub Actions job timeout (10 minutes)
3. Individual test fixtures

## Debugging Failed Tests

### View detailed output

```bash
pytest -vv --tb=long
```

### Run single test with logging

```bash
pytest tests/test_api_flow.py::test_create_invoice_success -vv -s
```

### Debug with pdb

```bash
pytest --pdb
```

### Check coverage

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Common Issues

### Tests Hanging

**Cause:** Background tasks not disabled

**Solution:** Ensure `TESTING=true` environment variable is set

### Database Errors

**Cause:** Database not properly isolated

**Solution:** Use `db_session` fixture, which creates fresh database for each test

### Import Errors

**Cause:** Missing dependencies

**Solution:**
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx aiosqlite
```

### CSRF Errors

**Cause:** Missing CSRF token in test

**Solution:**
```python
checkout_response = await client.get(f"/checkout/{payment_id}")
csrf_token = checkout_response.cookies.get("csrf_token")

response = await client.post(
    "/api/pay/...",
    data={"csrf_token": csrf_token, ...},
    cookies={"csrf_token": csrf_token}
)
```

## Test Performance

Current performance metrics:

- **Total tests:** 50+
- **Average runtime:** ~15 seconds
- **Coverage:** ~85%
- **Success rate:** 100% (when properly configured)

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure >80% coverage for new code
3. Run full test suite before committing
4. Update this README if adding new test files

### Test Checklist

- [ ] Unit tests for new functions
- [ ] Integration tests for new endpoints
- [ ] Error handling tests
- [ ] Edge case tests
- [ ] Documentation updated

## Manual Testing

For manual integration testing:

```bash
# Start server
uvicorn main:app --reload

# Run manual test
python tests/test_payment.py
```

This will:
1. Create a real invoice
2. Open browser for payment
3. Show webhook delivery
4. Verify full flow

