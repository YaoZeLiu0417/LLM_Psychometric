from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from collections.abc import MutableMapping
from typing import Any


_FINGERPRINT_KEY = secrets.token_bytes(32)
_UNLOCKED_KEY = "v2_researcher_unlocked"
_FINGERPRINT_STATE_KEY = "v2_researcher_access_fingerprint"
_INPUT_KEY = "v2_researcher_access_input"
_ERROR_KEY = "v2_researcher_access_error"


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


def clear_researcher_access(state: MutableMapping[str, Any]) -> None:
    state[_UNLOCKED_KEY] = False
    state[_FINGERPRINT_STATE_KEY] = None


def researcher_access_granted(state: MutableMapping[str, Any]) -> bool:
    current_fingerprint = live_access_fingerprint()
    stored_fingerprint = state.get(_FINGERPRINT_STATE_KEY)
    if (
        current_fingerprint is None
        or state.get(_UNLOCKED_KEY) is not True
        or not isinstance(stored_fingerprint, str)
        or not hmac.compare_digest(stored_fingerprint, current_fingerprint)
    ):
        clear_researcher_access(state)
        return False
    return True


def submit_researcher_access_code(state: MutableMapping[str, Any]) -> bool:
    submitted = str(state.get(_INPUT_KEY, ""))
    fingerprint = live_access_fingerprint()
    accepted = fingerprint is not None and verify_live_access_code(submitted)
    state[_INPUT_KEY] = ""
    if accepted:
        state[_UNLOCKED_KEY] = True
        state[_FINGERPRINT_STATE_KEY] = fingerprint
        state[_ERROR_KEY] = None
    else:
        clear_researcher_access(state)
        state[_ERROR_KEY] = "Access code not recognized."
    return accepted
