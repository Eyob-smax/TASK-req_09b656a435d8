"""
Pure audit helpers: field-diff sanitization + sensitive-key redaction.
"""
from src.security.audit import REDACTED, diff_fields, redact_sensitive


def test_diff_unchanged_fields_excluded():
    out = diff_fields({"a": 1, "b": 2}, {"a": 1, "b": 3})
    assert "a" not in out
    assert out["b"] == {"before": 2, "after": 3}


def test_diff_added_and_removed_fields():
    out = diff_fields({"a": 1}, {"b": 2})
    assert out["a"] == {"before": 1, "after": None}
    assert out["b"] == {"before": None, "after": 2}


def test_diff_sensitive_keys_redacted():
    out = diff_fields(
        {"password": "old-12345"},
        {"password": "new-67890"},
    )
    assert out["password"] == {"before": REDACTED, "after": REDACTED}


def test_diff_custom_sensitive_keys():
    out = diff_fields(
        {"internal_token": "a"},
        {"internal_token": "b"},
        sensitive_keys={"internal_token"},
    )
    assert out["internal_token"] == {"before": REDACTED, "after": REDACTED}


def test_redact_sensitive_recurses_into_dicts():
    payload = {
        "username": "alice",
        "password": "p@ssw0rd-long-enough",
        "nested": {
            "refresh_token": "abc",
            "ok": "visible",
        },
        "array": [{"access_token": "xyz"}, {"ok": 1}],
    }
    out = redact_sensitive(payload)
    assert out is not None
    assert out["username"] == "alice"
    assert out["password"] == REDACTED
    assert out["nested"]["refresh_token"] == REDACTED
    assert out["nested"]["ok"] == "visible"
    assert out["array"][0]["access_token"] == REDACTED
    assert out["array"][1]["ok"] == 1


def test_redact_sensitive_handles_none():
    assert redact_sensitive(None) is None


def test_redact_public_key_pem():
    out = redact_sensitive({"public_key_pem": "-----BEGIN PUBLIC KEY-----..."})
    assert out is not None
    assert out["public_key_pem"] == REDACTED


def test_redact_case_insensitive_keys():
    out = redact_sensitive({"PASSWORD": "secret"})
    assert out is not None
    assert out["PASSWORD"] == REDACTED
