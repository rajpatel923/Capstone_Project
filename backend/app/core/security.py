import hashlib
import hmac

import pyotp
from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions, Requestish
from cryptography.fernet import Fernet

from app.core.config import settings

# ---------------------------------------------------------------------------
# Clerk client (singleton)
# ---------------------------------------------------------------------------

_clerk = Clerk(bearer_auth=settings.clerk_secret_key)


def authenticate_clerk_request(request: Requestish) -> str:
    """Verify a Clerk session JWT; return Clerk user_id."""
    payload = get_clerk_payload(request)
    return payload["sub"]


def get_clerk_payload(request: Requestish) -> dict:
    """Verify a Clerk session JWT; return the full decoded payload."""
    opts = AuthenticateRequestOptions(
        authorized_parties=settings.cors_origins,
        jwt_key=settings.clerk_jwt_key or None,
    )
    state = _clerk.authenticate_request(request, opts)
    if not state.is_signed_in:
        raise ValueError("Request is not signed in")
    return state.payload


def get_clerk_user_role(user_id: str) -> str | None:
    """Fetch publicMetadata.role for a user via the Clerk backend API."""
    user = _clerk.users.get(user_id=user_id)
    return (user.public_metadata or {}).get("role")


# ---------------------------------------------------------------------------
# TOTP
# ---------------------------------------------------------------------------

def generate_totp_secret() -> str:
    return pyotp.random_base32()


TOTP_INTERVAL = 60  # seconds per code window


def get_provisioning_uri(secret: str, member_id: str, issuer: str = "CTF Fridge") -> str:
    return pyotp.TOTP(secret, interval=TOTP_INTERVAL).provisioning_uri(name=member_id, issuer_name=issuer)


def verify_totp(encrypted_secret: str, code: str) -> bool:
    secret = decrypt_totp_secret(encrypted_secret)
    totp = pyotp.TOTP(secret, interval=TOTP_INTERVAL)
    return totp.verify(code, valid_window=1)


# ---------------------------------------------------------------------------
# Fernet encryption for TOTP secrets
# ---------------------------------------------------------------------------

def _fernet() -> Fernet:
    return Fernet(settings.totp_encryption_key.encode())


def encrypt_totp_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_totp_secret(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode()).decode()


# ---------------------------------------------------------------------------
# HMAC webhook signature verification
# ---------------------------------------------------------------------------

def verify_hmac_signature(body: bytes, signature_header: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    provided = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, provided)


# ---------------------------------------------------------------------------
# Device API key
# ---------------------------------------------------------------------------

def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()
