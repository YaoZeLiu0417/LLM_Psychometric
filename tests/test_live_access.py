from psychometric_v2.live_access import (
    clear_researcher_access,
    live_access_fingerprint,
    live_access_configured,
    researcher_access_granted,
    submit_researcher_access_code,
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


def test_researcher_access_grant_stores_no_plaintext_and_rotates(
    monkeypatch,
) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "test-only-access-a")
    state: dict[str, object] = {
        "v2_researcher_access_input": "test-only-access-a"
    }

    assert submit_researcher_access_code(state) is True
    assert researcher_access_granted(state) is True
    assert state["v2_researcher_access_input"] == ""
    assert "test-only-access-a" not in repr(state)

    monkeypatch.setenv("LIVE_ACCESS_CODE", "test-only-access-b")
    assert researcher_access_granted(state) is False
    assert state["v2_researcher_unlocked"] is False
    assert state["v2_researcher_access_fingerprint"] is None


def test_researcher_access_rejects_and_clears_input(monkeypatch) -> None:
    monkeypatch.setenv("LIVE_ACCESS_CODE", "test-only-access-a")
    state: dict[str, object] = {"v2_researcher_access_input": "wrong"}

    assert submit_researcher_access_code(state) is False
    assert state["v2_researcher_access_input"] == ""
    assert state["v2_researcher_access_error"] == "Access code not recognized."
    assert researcher_access_granted(state) is False


def test_researcher_access_fails_closed_without_configured_code(monkeypatch) -> None:
    monkeypatch.delenv("LIVE_ACCESS_CODE", raising=False)
    state: dict[str, object] = {
        "v2_researcher_unlocked": True,
        "v2_researcher_access_fingerprint": "stale-fingerprint",
    }

    assert researcher_access_granted(state) is False
    assert state["v2_researcher_unlocked"] is False
    assert state["v2_researcher_access_fingerprint"] is None


def test_clear_researcher_access_does_not_create_raw_code_state() -> None:
    state: dict[str, object] = {}

    clear_researcher_access(state)

    assert state == {
        "v2_researcher_unlocked": False,
        "v2_researcher_access_fingerprint": None,
    }
