from __future__ import annotations

import hmac
import os


def _configured_code() -> str:
    return os.getenv("LIVE_ACCESS_CODE", "").strip()


def live_access_configured() -> bool:
    return bool(_configured_code())


def verify_live_access_code(submitted: str) -> bool:
    configured = _configured_code()
    candidate = submitted.strip()
    return bool(configured) and hmac.compare_digest(
        candidate.encode("utf-8"), configured.encode("utf-8")
    )
