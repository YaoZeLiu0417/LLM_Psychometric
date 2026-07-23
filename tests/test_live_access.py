from psychometric_v2.live_access import (
    live_access_fingerprint,
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


def test_live_access_accepts_exact_unicode_configured_code(monkeypatch) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "mi-ma-2026-密码")

    assert verify_live_access_code("mi-ma-2026-密码") is True


def test_live_access_rejects_wrong_unicode_configured_code(monkeypatch) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "mi-ma-2026-密码")

    assert verify_live_access_code("mi-ma-2027-密码") is False


def test_live_access_rejects_whitespace_only_configured_code(monkeypatch) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "   ")

    assert live_access_configured() is False
    assert verify_live_access_code("anything") is False


def test_live_access_trims_configured_and_submitted_codes(monkeypatch) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "  job-talk-2026  ")

    assert verify_live_access_code("  job-talk-2026  ") is True


def test_live_access_fingerprint_is_absent_without_configured_code(
    monkeypatch,
) -> None:
    monkeypatch.delenv("LIVE_ACCESS_CODE", raising=False)

    assert live_access_fingerprint() is None


def test_live_access_fingerprint_is_absent_for_blank_configured_code(
    monkeypatch,
) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "   ")

    assert live_access_fingerprint() is None


def test_live_access_fingerprint_is_stable_for_normalized_code(monkeypatch) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "  test-only-access-a  ")
    padded_fingerprint = live_access_fingerprint()
    monkeypatch.setenv("LIVE_ACCESS_CODE", "test-only-access-a")

    assert live_access_fingerprint() == padded_fingerprint
    assert len(padded_fingerprint or "") == 64


def test_live_access_fingerprint_changes_on_direct_rotation(monkeypatch) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "test-only-access-a")
    initial_fingerprint = live_access_fingerprint()
    monkeypatch.setenv("LIVE_ACCESS_CODE", "test-only-access-b")

    assert live_access_fingerprint() != initial_fingerprint


def test_live_access_fingerprint_does_not_expose_plaintext(monkeypatch) -> None:
    plaintext = "test-only-secret-code-visible-marker"
    monkeypatch.setenv("LIVE_ACCESS_CODE", plaintext)
    fingerprint = live_access_fingerprint()

    assert fingerprint is not None
    assert fingerprint != plaintext
    assert plaintext not in fingerprint
