"""Authentication and normalization helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta

from config.settings import Settings

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000
MIN_PASSWORD_LENGTH = 8


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_ticker(ticker: str) -> str:
    normalized = ticker.strip().upper()
    if not normalized or len(normalized) > 10 or not re.fullmatch(r"[A-Z0-9.-]+", normalized):
        raise ValueError("Ticker must be 1-10 characters using letters, numbers, dots, or dashes.")
    return normalized


def validate_email(email: str) -> str:
    normalized = normalize_email(email)
    if not normalized or "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise ValueError("Please enter a valid email address.")
    return normalized


def validate_password(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")
    return password


def hash_password(password: str) -> str:
    validate_password(password)
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(derived).decode("ascii")
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt_b64}${hash_b64}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        scheme, iterations_text, salt_b64, hash_b64 = encoded_hash.split("$", 3)
        if scheme != PASSWORD_SCHEME:
            return False
        iterations = int(iterations_text)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(hash_b64.encode("ascii"))
    except (TypeError, ValueError):
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(candidate, expected)


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_session_expiry(settings: Settings) -> datetime:
    return datetime.utcnow() + timedelta(days=settings.auth_session_days)
