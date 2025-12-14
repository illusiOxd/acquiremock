# 🧪 AcquireMock Testing Guide

Comprehensive guide to testing the AcquireMock payment gateway.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov pytest-timeout httpx aiosqlite

# 2. Run tests
pytest

# 3. View results
# ✅ All tests should pass
# 📊 Coverage report displayed
```

## Test Suite Overview

| Test File | Tests | Coverage | Purpose |
|-----------|-------|----------|---------|
| `test_api_flow.py` | 20+ | 85% | API endpoints, auth, webhooks |
| `test_integration.py` | 15+ | 90% | End-to-end payment flows |
| `test_services.py` | 15+ | 95% | Utilities, crypto, sanitization |
| **Total** | **50+** | **~85%** | **Full coverage** |

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific file
pytest tests/test_api_flow.py

# Run specific test
pytest tests/test_api_flow.py::test_create_invoice_success

# Run with coverage
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Advanced Options

```bash
# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Run failed tests only
pytest --lf

# Debug mode
pytest --pdb

# Parallel execution (if pytest-xdist installed)
pytest -n auto
```

## Test Configuration

### Environment Variables

Tests automatically configure:

```bash
TESTING=true                      # Disables background tasks
DATABASE_URL=sqlite+aiosqlite:///:memory:  # In-memory database
WEBHOOK_SECRET=test_secret...     # Test webhook secret
BASE_URL=http://test              # Test base URL
```

### pytest.ini

```ini
[pytest]
pythonpath = .
asyncio_mode = auto
addopts = --ignore=tests/test_payment.py -v --tb=short
timeout = 30
```

## What's Tested

### ✅ Core Payment Flow

- [x] Invoice creation
- [x] Checkout page loading
- [x] Card validation
- [x] OTP verification
- [x] Payment completion
- [x] Success page display
- [x] Webhook delivery

### ✅ Security

- [x] CSRF protection
- [x] XSS prevention
- [x] Input sanitization
- [x] Webhook signature verification
- [x] Data hashing (bcrypt)
- [x] Rate limiting

### ✅ User Features

- [x] Card saving
- [x] Saved card payment
- [x] Transaction history
- [x] Multi-language support
- [x] Dark mode
- [x] Returning user flow

### ✅ Error Handling

- [x] Invalid card numbers
- [x] Expired payments
- [x] Already paid payments
- [x] Missing CSRF tokens
- [x] Invalid OTP codes
- [x] 404 errors

### ✅ Edge Cases

- [x] Concurrent payments
- [x] Multiple users
- [x] Duplicate references
- [x] Payment expiration
- [x] Idempotency

### ✅ Services & Utils

- [x] OTP generation
- [x] CSRF token generation
- [x] Webhook signing
- [x] Input cleaning
- [x] Data encryption

## Test Architecture

### Fixtures

#### `db_session`
Provides isolated in-memory database:

```python
async def test_example(db_session: AsyncSession):
    payment = Payment(id="test", ...)
    db_session.add(payment)
    await db_session.commit()
```

#### `client`
Provides HTTP test client:

```python
async def test_example(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
```

### Test Isolation

- Each test gets fresh database
- No shared state between tests
- Background tasks disabled
- Timeouts prevent hanging

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Push to `main`/`master`
- Pull requests

```yaml
name: Run Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - run: pytest --cov=app
```

### Status Badge

Add to README.md:

```markdown
[![Tests](https://github.com/yourusername/acquiremock/workflows/Run%20Tests/badge.svg)](https://github.com/yourusername/acquiremock/actions)
```

## Writing New Tests

### Template

```python
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_my_feature(client: AsyncClient):
    """Test description."""
    # Arrange
    payload = {"key": "value"}
    
    # Act
    response = await client.post("/endpoint", json=payload)
    
    # Assert
    assert response.status_code == 200
    assert response.json()["result"] == "expected"
```

### Best Practices

1. **Use descriptive names:** `test_payment_with_valid_card_succeeds`
2. **Follow AAA pattern:** Arrange, Act, Assert
3. **Test one thing:** Each test should verify one behavior
4. **Use fixtures:** Reuse common setup code
5. **Add docstrings:** Explain what the test verifies
6. **Handle async:** Always use `async def` and `await`

### Example: Testing New Endpoint

```python
async def test_new_endpoint_success(client: AsyncClient):
    """Test new endpoint returns correct data."""
    response = await client.get("/api/new-endpoint")
    
    assert response.status_code == 200
    data = response.json()
    assert "key" in data
    assert data["key"] == "expected_value"

async def test_new_endpoint_validation(client: AsyncClient):
    """Test new endpoint validates input."""
    response = await client.post(
        "/api/new-endpoint",
        json={"invalid": "data"}
    )
    
    assert response.status_code == 422  # Validation error
```

## Coverage Report

### Generate Report

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Current Coverage

```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
app/api/routes/auth.py                    25      2    92%
app/api/routes/checkout.py                42      3    93%
app/api/routes/payments.py               120     15    88%
app/security/crypto.py                    20      1    95%
app/security/sanitizer.py                 10      0   100%
app/services/webhook_service.py           45      5    89%
-----------------------------------------------------------
TOTAL                                     500     40    85%
```

### Coverage Goals

- ✅ Minimum: 80%
- ✅ Target: 85%
- 🎯 Ideal: 90%+

## Debugging Tests

### Failed Test

```bash
# Show full traceback
pytest -vv --tb=long

# Show local variables
pytest -l

# Debug with pdb
pytest --pdb

# Run only failed
pytest --lf
```

### Hanging Test

```bash
# Check which test is hanging
pytest -v --timeout=10

# Run with logging
pytest -v -s --log-cli-level=DEBUG
```

### Database Issues

```bash
# Verify database isolation
pytest tests/test_api_flow.py::test_create_invoice_success -vv
```

## Performance

### Benchmarks

```bash
# Run with timing
pytest --durations=10

# Example output:
# 0.15s test_complete_payment_flow
# 0.08s test_create_invoice_success
# 0.05s test_health_check
```

### Optimization Tips

1. Use in-memory database (already done)
2. Disable background tasks (already done)
3. Mock external services (webhooks)
4. Parallel execution: `pytest -n auto`

## Common Issues

### Issue: Tests Hang

**Cause:** Background tasks not disabled

**Solution:**
```bash
export TESTING=true
pytest
```

### Issue: Import Errors

**Cause:** Missing dependencies

**Solution:**
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx aiosqlite
```

### Issue: Database Locked

**Cause:** Concurrent access to SQLite

**Solution:** Tests already use `:memory:` database

### Issue: CSRF Errors

**Cause:** Missing CSRF token

**Solution:**
```python
checkout = await client.get(f"/checkout/{payment_id}")
csrf = checkout.cookies.get("csrf_token")

await client.post(
    "/api/pay/...",
    data={"csrf_token": csrf, ...},
    cookies={"csrf_token": csrf}
)
```

## Manual Testing

For manual end-to-end testing:

```bash
# 1. Start server
uvicorn main:app --reload

# 2. Run manual test
python tests/test_payment.py
```

This will:
1. Create real invoice
2. Open browser for payment
3. Show OTP code in console
4. Verify webhook delivery

## Test Data

### Test Card Numbers

| Card | Result |
|------|--------|
| `4444 4444 4444 4444` | ✅ Success |
| Any other number | ❌ Insufficient Funds |

### Test Emails

Use any email address. OTP codes printed to console if SMTP not configured.

### Test Amounts

Use any amount in cents (e.g., `5000` = $50.00)

## Continuous Improvement

### Adding Tests Checklist

When adding new feature:

- [ ] Write unit tests for functions
- [ ] Write integration tests for endpoints
- [ ] Test error cases
- [ ] Test edge cases
- [ ] Verify coverage >80%
- [ ] Update documentation

### Code Review Checklist

- [ ] All tests pass
- [ ] Coverage maintained/improved
- [ ] No flaky tests
- [ ] Descriptive test names
- [ ] No commented-out tests

## Resources

- **Pytest Docs:** https://docs.pytest.org/
- **pytest-asyncio:** https://pytest-asyncio.readthedocs.io/
- **httpx Testing:** https://www.python-httpx.org/advanced/#calling-into-python-web-apps
- **SQLAlchemy Testing:** https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
---

**Happy Testing! 🎉**

For questions or issues, please open a GitHub issue.