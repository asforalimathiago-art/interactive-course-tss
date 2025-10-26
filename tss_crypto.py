"""
Hardened TSS crypto module with typing and clear error handling.
Provides threshold secret sharing for payload encryption.
"""

import base64
import hashlib
import json
import os
from typing import Any, Dict, List, Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

try:
    from secretsharing import PlaintextToHexSecretSharer as SSS

    SECRETSHARING_AVAILABLE = True
except ImportError:
    SSS = None
    SECRETSHARING_AVAILABLE = False


class SecretSharingUnavailableError(RuntimeError):
    """Raised when secretsharing library is not available."""

    def __init__(self):
        super().__init__(
            "The 'secretsharing' library is not installed. "
            "Install it with: pip install secretsharing"
        )


def base64_encode(data: bytes) -> str:
    """Encode bytes to base64 string."""
    return base64.b64encode(data).decode()


def base64_decode(data: str) -> bytes:
    """Decode base64 string to bytes."""
    return base64.b64decode(data.encode())


def encrypt_payload(payload: bytes) -> Tuple[Dict[str, Any], bytes]:
    """
    Encrypt payload using AES-GCM.

    Args:
        payload: Raw bytes to encrypt

    Returns:
        Tuple of (cipher artifact dict, encryption key)
    """
    key = AESGCM.generate_key(bit_length=256)
    aes = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aes.encrypt(nonce, payload, None)

    artifact = {
        "ciphertext_b64": base64_encode(ciphertext),
        "meta": {
            "alg": "AES-GCM",
            "nonce": base64_encode(nonce),
            "aad": None,
            "v": "1",
        },
    }

    return artifact, key


def decrypt_payload(artifact: Dict[str, Any], key: bytes) -> bytes:
    """
    Decrypt payload using AES-GCM.

    Args:
        artifact: Cipher artifact containing ciphertext and metadata
        key: Encryption key

    Returns:
        Decrypted payload bytes
    """
    aes = AESGCM(key)
    nonce = base64_decode(artifact["meta"]["nonce"])
    ciphertext = base64_decode(artifact["ciphertext_b64"])
    return aes.decrypt(nonce, ciphertext, None)


def split_key_shamir(key: bytes, threshold: int = 2, parts: int = 3) -> List[str]:
    """
    Split encryption key using Shamir's Secret Sharing.

    Args:
        key: Encryption key to split
        threshold: Minimum shares needed to reconstruct
        parts: Total number of shares to create

    Returns:
        List of share strings

    Raises:
        SecretSharingUnavailableError: If secretsharing library not installed
    """
    if not SECRETSHARING_AVAILABLE or SSS is None:
        raise SecretSharingUnavailableError()

    return SSS.split_secret(key.hex(), threshold, parts)


def combine_shares_shamir(shares: List[str]) -> bytes:
    """
    Combine Shamir shares to reconstruct key.

    Args:
        shares: List of share strings

    Returns:
        Reconstructed encryption key

    Raises:
        SecretSharingUnavailableError: If secretsharing library not installed
    """
    if not SECRETSHARING_AVAILABLE or SSS is None:
        raise SecretSharingUnavailableError()

    return bytes.fromhex(SSS.recover_secret(shares))


def wrap_share(share: str, key_id: str) -> str:
    """
    Wrap a share for storage/transmission.

    Args:
        share: Share string to wrap
        key_id: Key identifier (unused in current implementation)

    Returns:
        Base64-encoded wrapped share
    """
    return base64_encode(share.encode())


def unwrap_share(wrapped: str, key_id: str) -> str:
    """
    Unwrap a share from storage/transmission format.

    Args:
        wrapped: Wrapped share string
        key_id: Key identifier (unused in current implementation)

    Returns:
        Original share string
    """
    return base64_decode(wrapped).decode()


def tss_create(payload: Dict[str, Any], threshold: int = 2) -> Dict[str, Any]:
    """
    Create TSS-protected payload.

    Encrypts the payload and splits the encryption key using threshold
    secret sharing among three default roles: user, operator, regulator.

    Args:
        payload: Dictionary payload to protect
        threshold: Minimum shares needed to decrypt (default 2)

    Returns:
        Dictionary containing cipher artifact, shares, and payload hash

    Raises:
        SecretSharingUnavailableError: If secretsharing library not installed
    """
    # Serialize and encrypt
    raw_bytes = json.dumps(payload).encode()
    artifact, key = encrypt_payload(raw_bytes)

    # Split key into shares
    shares = split_key_shamir(key, threshold, 3)
    roles = ["user", "operator", "regulator"]

    # Wrap shares for each role
    wrapped_shares = [
        {"owner_role": role, "wrapped_share": wrap_share(share, f"kfp::{role}")}
        for role, share in zip(roles, shares)
    ]

    # Compute payload hash
    payload_hash = hashlib.sha256(raw_bytes).hexdigest()

    return {"cipher": artifact, "shares": wrapped_shares, "payload_hash": payload_hash}


def tss_reconstruct(
    cipher: Dict[str, Any], provided_roles: Dict[str, str]
) -> Dict[str, Any]:
    """
    Reconstruct TSS-protected payload.

    Args:
        cipher: Cipher artifact from tss_create
        provided_roles: Dict mapping role names to wrapped shares

    Returns:
        Decrypted payload dictionary

    Raises:
        SecretSharingUnavailableError: If secretsharing library not installed
    """
    # Unwrap shares
    plain_shares = [
        unwrap_share(wrapped, f"kfp::{role}")
        for role, wrapped in provided_roles.items()
    ]

    # Reconstruct key
    key = combine_shares_shamir(plain_shares)

    # Decrypt payload
    decrypted = decrypt_payload(cipher, key)
    return json.loads(decrypted.decode())
