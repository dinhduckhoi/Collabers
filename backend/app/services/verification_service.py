"""Email verification service."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.verification import EmailVerification, VerificationRateLimit, VerificationType
from app.models import User
from app.core.verification_security import (
    generate_verification_data,
    verify_token_hash,
    is_expired,
    hash_token,
    mask_email,
    MAX_OTP_ATTEMPTS,
    OTP_EXPIRY_MINUTES,
    LINK_EXPIRY_MINUTES,
)
from app.services.email_service import send_verification_email, send_password_reset_email

logger = logging.getLogger(__name__)


# Rate limiting configuration
RATE_LIMIT_RESEND = 3  # Max resend requests per window
RATE_LIMIT_VERIFY = 10  # Max verification attempts per window
RATE_LIMIT_WINDOW_MINUTES = 15  # Window duration


class VerificationError(Exception):
    """Base exception for verification errors."""
    pass


class RateLimitExceeded(VerificationError):
    """Raised when rate limit is exceeded."""
    pass


class InvalidOTP(VerificationError):
    """Raised when OTP is invalid."""
    pass


class ExpiredOTP(VerificationError):
    """Raised when OTP has expired."""
    pass


class MaxAttemptsExceeded(VerificationError):
    """Raised when max OTP attempts exceeded."""
    pass


class InvalidToken(VerificationError):
    """Raised when link token is invalid."""
    pass


class ExpiredToken(VerificationError):
    """Raised when link token has expired."""
    pass


class AlreadyVerified(VerificationError):
    """Raised when email is already verified."""
    pass


class TokenAlreadyUsed(VerificationError):
    """Raised when token has already been used."""
    pass


async def check_rate_limit(
    db: AsyncSession,
    identifier: str,
    action: str,
    max_attempts: int
) -> bool:
    """Check rate limit. Returns True if allowed."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
    
    # Find existing rate limit record
    result = await db.execute(
        select(VerificationRateLimit).where(
            and_(
                VerificationRateLimit.identifier == identifier,
                VerificationRateLimit.action == action,
                VerificationRateLimit.window_start > window_start
            )
        )
    )
    rate_limit = result.scalar_one_or_none()
    
    if rate_limit:
        if rate_limit.attempt_count >= max_attempts:
            return False
        rate_limit.attempt_count += 1
    else:
        # Clean up old records and create new one
        await db.execute(
            delete(VerificationRateLimit).where(
                and_(
                    VerificationRateLimit.identifier == identifier,
                    VerificationRateLimit.action == action
                )
            )
        )
        rate_limit = VerificationRateLimit(
            identifier=identifier,
            action=action,
            attempt_count=1,
            window_start=now
        )
        db.add(rate_limit)
    
    await db.commit()
    return True


async def create_email_verification(
    db: AsyncSession,
    user: User,
    verification_type: VerificationType = VerificationType.EMAIL_VERIFICATION
) -> Tuple[str, str]:
    """Create verification record and send email. Returns (otp, link_token)."""
    # Check rate limit for resending
    if not await check_rate_limit(db, str(user.id), "resend_otp", RATE_LIMIT_RESEND):
        raise RateLimitExceeded("Too many verification requests. Please wait before trying again.")
    
    # Invalidate existing verifications
    await db.execute(
        delete(EmailVerification).where(
            and_(
                EmailVerification.user_id == user.id,
                EmailVerification.verification_type == verification_type
            )
        )
    )
    
    # Generate new verification data
    otp, otp_hash, link_token, link_token_hash, otp_expires_at, link_expires_at = generate_verification_data()
    
    # Create verification record
    verification = EmailVerification(
        user_id=user.id,
        otp_hash=otp_hash,
        otp_expires_at=otp_expires_at,
        link_token_hash=link_token_hash,
        link_expires_at=link_expires_at,
        verification_type=verification_type,
    )
    db.add(verification)
    await db.commit()
    
    # Send verification email
    if verification_type == VerificationType.EMAIL_VERIFICATION:
        await send_verification_email(user.email, otp, link_token)
    else:
        await send_password_reset_email(user.email, otp, link_token)
    
    logger.info(f"Verification created for user {mask_email(user.email)}")
    
    return otp, link_token


async def verify_otp(
    db: AsyncSession,
    user: User,
    otp: str,
    verification_type: VerificationType = VerificationType.EMAIL_VERIFICATION
) -> bool:
    """Verify OTP code."""
    # Check rate limit
    if not await check_rate_limit(db, str(user.id), "verify_otp", RATE_LIMIT_VERIFY):
        raise RateLimitExceeded("Too many verification attempts. Please wait before trying again.")
    
    # Find verification record
    result = await db.execute(
        select(EmailVerification).where(
            and_(
                EmailVerification.user_id == user.id,
                EmailVerification.verification_type == verification_type,
                EmailVerification.is_used == False
            )
        )
    )
    verification = result.scalar_one_or_none()
    
    if not verification:
        raise InvalidOTP("No pending verification found.")
    
    # Check if already used
    if verification.is_used:
        raise TokenAlreadyUsed("This verification has already been used.")
    
    # Check max attempts
    if verification.otp_attempts >= MAX_OTP_ATTEMPTS:
        raise MaxAttemptsExceeded("Maximum verification attempts exceeded. Please request a new code.")
    
    # Increment attempts first (before validation)
    verification.otp_attempts += 1
    await db.commit()
    
    # Check expiry
    if is_expired(verification.otp_expires_at):
        raise ExpiredOTP("Verification code has expired. Please request a new code.")
    
    # Constant-time comparison
    if not verify_token_hash(otp, verification.otp_hash):
        remaining = MAX_OTP_ATTEMPTS - verification.otp_attempts
        if remaining > 0:
            raise InvalidOTP(f"Invalid verification code. {remaining} attempts remaining.")
        else:
            raise MaxAttemptsExceeded("Maximum verification attempts exceeded. Please request a new code.")
    
    # Success - mark as used and verify user
    verification.is_used = True
    
    if verification_type == VerificationType.EMAIL_VERIFICATION:
        user.email_verified = True
        logger.info(f"Email verified for user {mask_email(user.email)} via OTP")
    
    await db.commit()
    return True


async def verify_link_token(
    db: AsyncSession,
    token: str,
    verification_type: VerificationType = VerificationType.EMAIL_VERIFICATION
) -> Optional[User]:
    """Verify link token. Returns User if successful."""
    token_hash = hash_token(token)
    
    # Find verification record
    result = await db.execute(
        select(EmailVerification).where(
            and_(
                EmailVerification.link_token_hash == token_hash,
                EmailVerification.verification_type == verification_type,
                EmailVerification.is_used == False
            )
        )
    )
    verification = result.scalar_one_or_none()
    
    if not verification:
        raise InvalidToken("Invalid or expired verification link.")
    
    # Check if already used
    if verification.is_used:
        raise TokenAlreadyUsed("This verification link has already been used.")
    
    # Check expiry
    if is_expired(verification.link_expires_at):
        raise ExpiredToken("Verification link has expired. Please request a new one.")
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == verification.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise InvalidToken("User not found.")
    
    # Success - mark as used and verify user
    verification.is_used = True
    
    if verification_type == VerificationType.EMAIL_VERIFICATION:
        user.email_verified = True
        logger.info(f"Email verified for user {mask_email(user.email)} via link")
    
    await db.commit()
    return user


async def get_pending_verification(
    db: AsyncSession,
    user_id: int,
    verification_type: VerificationType = VerificationType.EMAIL_VERIFICATION
) -> Optional[EmailVerification]:
    """Get pending verification for a user."""
    result = await db.execute(
        select(EmailVerification).where(
            and_(
                EmailVerification.user_id == user_id,
                EmailVerification.verification_type == verification_type,
                EmailVerification.is_used == False
            )
        )
    )
    return result.scalar_one_or_none()


async def cleanup_expired_verifications(db: AsyncSession) -> int:
    """
    Clean up expired verification records.
    
    Should be run periodically via a background task.
    Returns count of deleted records.
    """
    now = datetime.now(timezone.utc)
    
    result = await db.execute(
        delete(EmailVerification).where(
            and_(
                EmailVerification.link_expires_at < now,
                EmailVerification.is_used == False
            )
        )
    )
    
    await db.commit()
    return result.rowcount
