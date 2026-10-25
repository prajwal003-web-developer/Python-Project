import hashlib
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError

ACCESS = "access"
REFRESH = "refresh"

_hasher = PasswordHasher()
# Used to equalise timing when the account does not exist (prevents user enumeration by latency).
DUMMY_HASH = _hasher.hash("timing-equalisation-placeholder")


# ---------- passwords ----------
def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def validate_password_strength(password: str) -> str:
    if not 8 <= len(password) <= 128:
        raise ValueError("Password must be between 8 and 128 characters")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain a lowercase letter")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain an uppercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain a digit")
    return password


# ---------- normalisation ----------
def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_username(username: str) -> str:
    return username.strip().lower()


# ---------- tokens ----------
def _encode(subject: str, token_type: str, ttl: timedelta) -> tuple[str, datetime]:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires = now + ttl
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": expires,
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm)
    return token, expires


def create_access_token(user_id: str) -> tuple[str, datetime]:
    return _encode(user_id, ACCESS, timedelta(minutes=get_settings().access_token_expire_minutes))


def create_refresh_token(user_id: str) -> tuple[str, datetime]:
    return _encode(user_id, REFRESH, timedelta(days=get_settings().refresh_token_expire_days))


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub", "type", "jti"]},
            leeway=10,
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("invalid_token", "Invalid or expired token") from exc
    if payload.get("type") != expected_type:
        raise UnauthorizedError("invalid_token", "Invalid or expired token")
    return payload


def hash_token(token: str) -> str:
    """Refresh tokens are stored only as SHA-256 digests."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def tokens_match(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode(), b.encode())
