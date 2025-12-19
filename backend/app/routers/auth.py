"""Authentication router."""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Request, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field

from app.routers.deps import DBSession, CurrentUser
from app.schemas import (
    UserCreate, UserLogin, TokenPair, TokenRefresh, UserResponse,
    PasswordResetRequest
)
from app.services import (
    create_user, get_user_by_email, authenticate_user,
    update_user_password
)
from app.services.verification_service import (
    create_email_verification,
    verify_otp,
    verify_link_token,
    RateLimitExceeded,
    InvalidOTP,
    ExpiredOTP,
    MaxAttemptsExceeded,
    InvalidToken,
    ExpiredToken,
    TokenAlreadyUsed,
)
from app.models.verification import VerificationType
from app.core.security import (
    create_access_token, create_refresh_token, decode_token
)
from app.core.verification_security import mask_email
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============== Schemas ==============

class OTPVerifyRequest(BaseModel):
    """Request body for OTP verification."""
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class RegisterResponse(BaseModel):
    """Response after successful registration."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    message: str
    email_verified: bool = False
    # Development only - remove in production
    dev_otp: Optional[str] = None
    dev_link_token: Optional[str] = None


# ============== Registration ==============

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, data: UserCreate, db: DBSession):
    """Register a new user and send verification email."""
    existing_user = await get_user_by_email(db, data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = await create_user(db, data.email, data.password)
    
    # Create verification and send email
    try:
        otp, link_token = await create_email_verification(
            db, user, VerificationType.EMAIL_VERIFICATION
        )
    except RateLimitExceeded as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    
    access_token = create_access_token(data={"sub": str(user.id)}, token_version=user.token_version)
    refresh_token = create_refresh_token(data={"sub": str(user.id)}, token_version=user.token_version)
    
    logger.info(f"New user registered: {mask_email(user.email)}")
    
    # In development, return OTP/token for testing (REMOVE IN PRODUCTION)
    response = RegisterResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        message="Registration successful. Please verify your email.",
        email_verified=False,
    )
    
    # Only include dev tokens in development mode (NEVER in production)
    if not settings.PRODUCTION and not settings.SMTP_HOST:
        response.dev_otp = otp
        response.dev_link_token = link_token
    
    return response


# ============== Login ==============

@router.post("/login", response_model=TokenPair)
async def login(request: Request, data: UserLogin, db: DBSession):
    """Login with email and password."""
    user = await authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)}, token_version=user.token_version)
    refresh_token = create_refresh_token(data={"sub": str(user.id)}, token_version=user.token_version)
    
    logger.info(f"User logged in: {mask_email(user.email)}")
    
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


# ============== Token Refresh ==============

@router.post("/refresh", response_model=TokenPair)
async def refresh_token(data: TokenRefresh, db: DBSession):
    """Refresh access token using refresh token."""
    payload = decode_token(data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


# ============== Current User Info ==============

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """Get current authenticated user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        last_active=current_user.last_active,
        account_status=current_user.account_status.value
    )


# ============== Resend Verification ==============

@router.post("/resend-verification")
async def resend_verification(current_user: CurrentUser, db: DBSession):
    """Resend verification email."""
    if current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    try:
        otp, link_token = await create_email_verification(
            db, current_user, VerificationType.EMAIL_VERIFICATION
        )
    except RateLimitExceeded as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    
    logger.info(f"Verification resent to: {mask_email(current_user.email)}")
    
    response = {"message": "Verification email sent. Check your inbox."}
    
    # Development only
    if not settings.SMTP_HOST:
        response["dev_otp"] = otp
        response["dev_link_token"] = link_token
    
    return response


# ============== OTP Verification ==============

@router.post("/verify-otp")
async def verify_otp_endpoint(
    data: OTPVerifyRequest,
    current_user: CurrentUser,
    db: DBSession
):
    """Verify email using OTP code."""
    if current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    try:
        await verify_otp(db, current_user, data.otp, VerificationType.EMAIL_VERIFICATION)
        logger.info(f"Email verified via OTP: {mask_email(current_user.email)}")
        return {"message": "Email verified successfully"}
        
    except RateLimitExceeded as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except (InvalidOTP, ExpiredOTP, MaxAttemptsExceeded, TokenAlreadyUsed) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============== Link Verification ==============

@router.get("/verify-link")
async def verify_link_endpoint(
    token: str = Query(..., min_length=32),
    db: DBSession = None
):
    """Verify email via link. Redirects to frontend with result."""
    try:
        user = await verify_link_token(db, token, VerificationType.EMAIL_VERIFICATION)
        if user:
            logger.info(f"Email verified via link: {mask_email(user.email)}")
            # Redirect to frontend with success
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/verify-email?status=success",
                status_code=status.HTTP_302_FOUND
            )
    except (InvalidToken, ExpiredToken, TokenAlreadyUsed) as e:
        logger.warning(f"Link verification failed: {type(e).__name__}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/verify-email?status=error&message={str(e)}",
            status_code=status.HTTP_302_FOUND
        )
    
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/verify-email?status=error",
        status_code=status.HTTP_302_FOUND
    )


# ============== Password Reset Request ==============

@router.post("/request-password-reset")
async def request_password_reset(request: Request, data: PasswordResetRequest, db: DBSession):
    """Request password reset email."""
    user = await get_user_by_email(db, data.email)
    
    if user:
        try:
            otp, link_token = await create_email_verification(
                db, user, VerificationType.PASSWORD_RESET
            )
            
            response = {
                "message": "If an account exists with this email, a password reset link has been sent."
            }
            
            # Development only - NEVER in production
            if not settings.PRODUCTION and not settings.SMTP_HOST:
                response["dev_otp"] = otp
                response["dev_link_token"] = link_token
            
            return response
            
        except RateLimitExceeded:
            pass  # Don't reveal rate limiting to prevent enumeration
    
    # Always return success to prevent email enumeration
    return {"message": "If an account exists with this email, a password reset link has been sent."}


# ============== Password Reset via OTP ==============

class PasswordResetOTPRequest(BaseModel):
    """Request body for password reset via OTP."""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str = Field(..., min_length=8)


@router.post("/reset-password-otp")
async def reset_password_otp(data: PasswordResetOTPRequest, db: DBSession):
    """Reset password using OTP code."""
    user = await get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or verification code"
        )
    
    try:
        await verify_otp(db, user, data.otp, VerificationType.PASSWORD_RESET)
        await update_user_password(db, user, data.new_password)
        logger.info(f"Password reset via OTP: {mask_email(user.email)}")
        return {"message": "Password reset successfully"}
        
    except RateLimitExceeded as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except (InvalidOTP, ExpiredOTP, MaxAttemptsExceeded, TokenAlreadyUsed) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============== Password Reset via Link ==============

class PasswordResetLinkRequest(BaseModel):
    """Request body for password reset via link token."""
    token: str = Field(..., min_length=32)
    new_password: str = Field(..., min_length=8)


@router.post("/reset-password-link")
async def reset_password_link(data: PasswordResetLinkRequest, db: DBSession):
    """Reset password using link token."""
    try:
        user = await verify_link_token(db, data.token, VerificationType.PASSWORD_RESET)
        if user:
            await update_user_password(db, user, data.new_password)
            logger.info(f"Password reset via link: {mask_email(user.email)}")
            return {"message": "Password reset successfully"}
            
    except (InvalidToken, ExpiredToken, TokenAlreadyUsed) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired reset token"
    )
