from __future__ import annotations

import hashlib
import hmac
import os
import secrets


_FINGERPRINT_KEY = secrets.token_bytes(32)


def _configured_code() -> str:
    return os.getenv("LIVE_ACCESS_CODE", "").strip()


def live_access_configured() -> bool:
    return bool(_configured_code())


def live_access_fingerprint() -> str | None:
    configured = _configured_code()
    if not configured:
        return None
    return hmac.new(
        _FINGERPRINT_KEY,
        configured.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_live_access_code(submitted: str) -> bool:
    configured = _configured_code()
    candidate = submitted.strip()
    return bool(configured) and hmac.compare_digest(
        candidate.encode("utf-8"), configured.encode("utf-8")
    )
