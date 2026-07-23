from psychometric_v2.live_access import (
    live_access_configured,
    verify_live_access_code,
)


def test_live_access_is_unavailable_without_configured_code(monkeypatch) -> None:
    monkeypatch.delenv("LIVE_ACCESS_CODE", raising=False)

    assert live_access_configured() is False
    assert verify_live_access_code("anything") is False


def test_live_access_rejects_wrong_configured_code(monkeypatch) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "job-talk-2026")

    assert live_access_configured() is True
    assert verify_live_access_code("wrong-code") is False


def test_live_access_accepts_exact_configured_code(monkeypatch) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "job-talk-2026")

    assert verify_live_access_code("job-talk-2026") is True
