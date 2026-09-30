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
    """Verify a Clerk session JWT from the request headers.

    Uses offline PEM verification if CLERK_JWT_KEY is set, otherwise
    falls back to online JWKS lookup handled by the SDK.
    Returns the Clerk user_id (sub claim).
    """
    opts = AuthenticateRequestOptions(
        authorized_parties=settings.cors_origins,
        jwt_key=settings.clerk_jwt_key or None,
    )
    state = _clerk.authenticate_request(request, opts)
    if not state.is_signed_in:
        raise ValueError("Request is not signed in")
    return state.payload["sub"]


# ---------------------------------------------------------------------------
# TOTP
# ---------------------------------------------------------------------------

def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_provisioning_uri(secret: str, member_id: str, issuer: str = "CTF Fridge") -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=member_id, issuer_name=issuer)


def verify_totp(encrypted_secret: str, code: str) -> bool:
    secret = decrypt_totp_secret(encrypted_secret)
    totp = pyotp.TOTP(secret)
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
