"""
Covers Argon2id hash/verify/needs_rehash semantics.
"""
from src.security.passwords import hash_password, needs_rehash, verify_password


def test_hash_verify_roundtrip():
    pwd = "correct horse battery staple"
    h = hash_password(pwd)
    assert h != pwd
    assert h.startswith("$argon2id$")
    assert verify_password(pwd, h) is True


def test_wrong_password_fails():
    pwd = "correct horse battery staple"
    h = hash_password(pwd)
    assert verify_password("incorrect horse battery!!!!!", h) is False


def test_unique_salts_produce_different_hashes():
    pwd = "correct horse battery staple"
    h1 = hash_password(pwd)
    h2 = hash_password(pwd)
    assert h1 != h2
    assert verify_password(pwd, h1) is True
    assert verify_password(pwd, h2) is True


def test_verify_against_empty_hash_returns_false():
    assert verify_password("anything anything", "") is False


def test_verify_against_malformed_hash_returns_false():
    assert verify_password("anything anything", "not-a-hash") is False


def test_needs_rehash_false_for_current_params():
    pwd = "correct horse battery staple"
    h = hash_password(pwd)
    assert needs_rehash(h) is False


def test_needs_rehash_true_for_malformed_hash():
    assert needs_rehash("garbage") is True
