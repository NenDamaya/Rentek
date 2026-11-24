"""
Módulo de autenticación: Hashing de contraseñas y gestión de tokens.
Usa solo stdlib (hashlib + hmac) para no agregar dependencias.
"""

import hashlib
import hmac
import os
import time
import secrets
from typing import Optional, Tuple

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "rentek-secret-key-change-in-production-2026")
TOKEN_EXPIRY_HOURS = 24  # 24 horas


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}${key.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, key_hex = stored.split("$", 1)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
        return hmac.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


def create_token(user_id: int, username: str) -> str:
    payload = f"{user_id}:{username}:{int(time.time())}"
    sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{payload}${sig}"


def verify_token(token: str) -> Optional[Tuple[int, str]]:
    try:
        parts = token.rsplit("$", 1)
        if len(parts) != 2:
            return None
        payload, sig = parts
        expected_sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, expected_sig):
            return None
        user_id_str, username, ts = payload.split(":", 2)
        if time.time() - int(ts) > TOKEN_EXPIRY_HOURS * 3600:
            return None
        return int(user_id_str), username
    except Exception:
        return None
