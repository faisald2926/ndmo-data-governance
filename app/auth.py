"""Authentication & role-based access control — standard library only.

Passwords: PBKDF2-HMAC-SHA256 with a per-user salt.
Tokens: compact HMAC-SHA256-signed tokens (JWT-like) with an expiry.
No external crypto dependencies, so it runs anywhere the app does.
"""
import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import settings

_PBKDF2_ROUNDS = 200_000
_bearer = HTTPBearer(auto_error=False)


# --- password hashing -------------------------------------------------------
def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(),
                                 bytes.fromhex(salt_hex), _PBKDF2_ROUNDS)
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:                              # noqa: BLE001
        return False


# --- tokens -----------------------------------------------------------------
def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def create_token(username: str, role: str) -> str:
    payload = {"sub": username, "role": role,
               "exp": int(time.time()) + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60}
    body = _b64(json.dumps(payload).encode())
    sig = _b64(hmac.new(settings.JWT_SECRET.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def decode_token(token: str) -> dict | None:
    try:
        body, sig = token.split(".")
        expected = _b64(hmac.new(settings.JWT_SECRET.encode(), body.encode(),
                                 hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_unb64(body))
        if int(payload.get("exp", 0)) < time.time():
            return None
        return payload
    except Exception:                              # noqa: BLE001
        return None


# --- FastAPI dependencies ---------------------------------------------------
def get_current_user(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    return {"username": payload["sub"], "role": payload["role"]}


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin privileges required")
    return user


# --- seeding ----------------------------------------------------------------
def seed_users() -> None:
    """Create the admin (and an optional demo viewer) if they don't exist."""
    from db import SessionLocal
    from models import User
    s = SessionLocal()
    try:
        if not s.query(User).filter_by(username=settings.ADMIN_USERNAME).first():
            s.add(User(username=settings.ADMIN_USERNAME,
                       password_hash=hash_password(settings.ADMIN_PASSWORD), role="admin"))
        if settings.SEED_DEMO_VIEWER and not s.query(User).filter_by(username="viewer").first():
            s.add(User(username="viewer",
                       password_hash=hash_password("viewer123"), role="viewer"))
        s.commit()
    finally:
        s.close()
