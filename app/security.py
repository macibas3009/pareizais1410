"""Paroļu jaukšana un sesiju marķieri (CR-4). Tikai Python standarta bibliotēka."""

from __future__ import annotations

import hashlib
import hmac
import secrets

# scrypt parametri: N=2^14, r=8, p=1 (OWASP minimums scrypt algoritmam)
_N, _R, _P, _DKLEN = 2**14, 8, 1, 32


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, n, r, p, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(digest_hex) // 2,
        )
    except ValueError:
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


# Izmanto, ja konts neeksistē, lai atbildes laiks neatklātu konta esamību
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
