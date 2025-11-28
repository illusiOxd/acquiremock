import secrets
import string

def generate_secure_otp(length: int = 4) -> str:
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)