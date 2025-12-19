"""
Verification Security Utilities

Cryptographically secure OTP and token generation with constant-time comparison.
"""
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Tuple


# Configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
LINK_TOKEN_BYTES = 32  # 256 bits of entropy
LINK_EXPIRY_MINUTES = 30
MAX_OTP_ATTEMPTS = 5


def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    otp = secrets.randbelow(10 ** OTP_LENGTH)
    return str(otp).zfill(OTP_LENGTH)


def generate_link_token() -> str:
    """Generate a URL-safe verification token."""
    return secrets.token_urlsafe(LINK_TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Hash token with SHA-256."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def verify_token_hash(token: str, stored_hash: str) -> bool:
    """Constant-time comparison of token hash."""
    computed_hash = hash_token(token)
    return hmac.compare_digest(computed_hash, stored_hash)


def generate_verification_data() -> Tuple[str, str, str, str, datetime, datetime]:
    """
    Generate both OTP and link token with their hashes and expiry times.
    
    Returns:
        Tuple of (otp, otp_hash, link_token, link_token_hash, otp_expires_at, link_expires_at)
    """
    now = datetime.now(timezone.utc)
    
    # Generate OTP
    otp = generate_otp()
    otp_hash = hash_token(otp)
    otp_expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)
    
    # Generate link token
    link_token = generate_link_token()
    link_token_hash = hash_token(link_token)
    link_expires_at = now + timedelta(minutes=LINK_EXPIRY_MINUTES)
    
    return otp, otp_hash, link_token, link_token_hash, otp_expires_at, link_expires_at


def is_expired(expires_at: datetime) -> bool:
    """Check if timestamp has expired."""
    now = datetime.now(timezone.utc)
    
    # If expires_at is naive, assume it's UTC
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    return now > expires_at


def mask_email(email: str) -> str:
    """
    Mask email for logging purposes.
    
    Example: 'user@example.com' -> 'u***@e***.com'
    """
    try:
        local, domain = email.split('@')
        domain_parts = domain.split('.')
        masked_local = local[0] + '***' if len(local) > 1 else '***'
        masked_domain = domain_parts[0][0] + '***' if len(domain_parts[0]) > 1 else '***'
        return f"{masked_local}@{masked_domain}.{domain_parts[-1]}"
    except (ValueError, IndexError):
        return '***@***.***'
