"""Temporary Ed25519 request proof for the Phase 02 prototype.

Q-12/Q-15 still own the production wire format, replay prevention, mTLS and
key lifecycle. This module deliberately stores and accepts public material only.
"""

import base64
from uuid import UUID

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class DeviceIdentityError(ValueError):
    """A malformed key or an invalid request proof."""


def decode_public_key(encoded_key: str) -> Ed25519PublicKey:
    try:
        raw_key = base64.b64decode(encoded_key.encode("ascii"), validate=True)
        return Ed25519PublicKey.from_public_bytes(raw_key)
    except (UnicodeEncodeError, ValueError) as error:
        raise DeviceIdentityError("Invalid device public key") from error


def request_payload(method: str, path: str, device_uuid: UUID) -> bytes:
    """Small, explicit prototype canonical form; no client-supplied MID."""
    return f"{method.upper()}\n{path}\n{device_uuid}".encode("ascii")


def verify_request_signature(
    encoded_key: str, encoded_signature: str, *, method: str, path: str, device_uuid: UUID
) -> None:
    try:
        signature = base64.b64decode(encoded_signature.encode("ascii"), validate=True)
        decode_public_key(encoded_key).verify(
            signature, request_payload(method, path, device_uuid)
        )
    except (UnicodeEncodeError, ValueError, InvalidSignature, DeviceIdentityError) as error:
        raise DeviceIdentityError("Invalid machine credential") from error
