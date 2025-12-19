"""
Email Verification Models

Stores hashed OTP codes and verification link tokens.
Both are single-use and auto-invalidated upon successful verification.
"""
import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.models import User


class VerificationType(enum.Enum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"


class EmailVerification(Base):
    """Stores hashed OTP and link tokens for email verification."""
    __tablename__ = "email_verifications"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # OTP fields (hashed)
    otp_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 hex = 64 chars
    otp_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    otp_attempts: Mapped[int] = mapped_column(Integer, default=0)
    
    # Link token fields (hashed)
    link_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 hex = 64 chars
    link_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Common fields
    verification_type: Mapped[VerificationType] = mapped_column(
        SQLEnum(VerificationType), 
        default=VerificationType.EMAIL_VERIFICATION
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationship
    user: Mapped["User"] = relationship("User", backref="verifications")
    
    # Indexes for efficient lookups
    __table_args__ = (
        Index('ix_email_verifications_user_id_type', 'user_id', 'verification_type'),
    )


class VerificationRateLimit(Base):
    """Rate limiting for verification actions."""
    __tablename__ = "verification_rate_limits"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  # user_id or IP
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # resend_otp, verify_otp, verify_link
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    
    __table_args__ = (
        Index('ix_rate_limit_identifier_action', 'identifier', 'action'),
    )
