"""
Tests for TSS crypto functionality.
"""

import pytest
from tss_crypto import (
    base64_encode,
    base64_decode,
    encrypt_payload,
    decrypt_payload,
    tss_create,
    tss_reconstruct,
    SecretSharingUnavailableError,
    SECRETSHARING_AVAILABLE,
)


def test_base64_encoding():
    """Test base64 encoding and decoding."""
    data = b"test data"
    encoded = base64_encode(data)
    decoded = base64_decode(encoded)
    assert decoded == data


def test_encrypt_decrypt():
    """Test payload encryption and decryption."""
    payload = b"secret message"
    artifact, key = encrypt_payload(payload)

    assert "ciphertext_b64" in artifact
    assert "meta" in artifact
    assert artifact["meta"]["alg"] == "AES-GCM"

    decrypted = decrypt_payload(artifact, key)
    assert decrypted == payload


@pytest.mark.skipif(
    not SECRETSHARING_AVAILABLE, reason="secretsharing library not installed"
)
def test_tss_create_reconstruct():
    """Test TSS creation and reconstruction."""
    payload = {"org_id": "test-org", "event_type": "test", "payload": {"key": "value"}}

    # Create TSS artifact
    artifact = tss_create(payload, threshold=2)

    assert "cipher" in artifact
    assert "shares" in artifact
    assert "payload_hash" in artifact
    assert len(artifact["shares"]) == 3

    # Test reconstruction with 2 shares
    provided_roles = {
        artifact["shares"][0]["owner_role"]: artifact["shares"][0]["wrapped_share"],
        artifact["shares"][1]["owner_role"]: artifact["shares"][1]["wrapped_share"],
    }

    reconstructed = tss_reconstruct(artifact["cipher"], provided_roles)
    assert reconstructed == payload


@pytest.mark.skipif(
    not SECRETSHARING_AVAILABLE, reason="secretsharing library not installed"
)
def test_tss_roles():
    """Test that default roles are created correctly."""
    payload = {"test": "data"}
    artifact = tss_create(payload)

    roles = {share["owner_role"] for share in artifact["shares"]}
    assert roles == {"user", "operator", "regulator"}


def test_secretsharing_error_message():
    """Test that SecretSharingUnavailableError has clear message."""
    error = SecretSharingUnavailableError()
    assert "secretsharing" in str(error).lower()
    assert "pip install" in str(error).lower()
