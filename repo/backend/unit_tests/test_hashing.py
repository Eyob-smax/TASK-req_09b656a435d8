"""
SHA-256 helpers against known vectors and streaming parity.
"""
import io

from src.security.hashing import (
    sha256_of_bytes,
    sha256_of_stream,
    verify_sha256_bytes,
    verify_sha256_stream,
)


EMPTY_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
ABC_HASH = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_hash_empty_bytes():
    assert sha256_of_bytes(b"") == EMPTY_HASH


def test_hash_known_vector_abc():
    assert sha256_of_bytes(b"abc") == ABC_HASH


def test_streaming_matches_one_shot():
    data = b"the quick brown fox jumps over the lazy dog" * 1024
    assert sha256_of_stream(io.BytesIO(data)) == sha256_of_bytes(data)


def test_streaming_boundary_safe():
    data = b"\x00" * (65536 * 3 + 17)  # odd size across multiple chunks
    stream_hash = sha256_of_stream(io.BytesIO(data))
    assert stream_hash == sha256_of_bytes(data)


def test_verify_bytes_true_and_false():
    data = b"abc"
    assert verify_sha256_bytes(data, ABC_HASH) is True
    assert verify_sha256_bytes(data, EMPTY_HASH) is False


def test_verify_bytes_case_insensitive():
    assert verify_sha256_bytes(b"abc", ABC_HASH.upper()) is True


def test_verify_bytes_empty_expected_false():
    assert verify_sha256_bytes(b"abc", "") is False


def test_verify_stream_true_and_false():
    assert verify_sha256_stream(io.BytesIO(b"abc"), ABC_HASH) is True
    assert verify_sha256_stream(io.BytesIO(b"xyz"), ABC_HASH) is False
