"""Email service for sending verification emails."""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings
from app.core.verification_security import mask_email

logger = logging.getLogger(__name__)


def get_verification_email_html(
    otp: str,
    verification_link: str,
    otp_expiry_minutes: int = 5,
    link_expiry_minutes: int = 30
) -> str:
    """Generate HTML email with OTP and verification link."""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email - Collabers</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; max-width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background-color: #4f46e5; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">Collabers</h1>
                            <p style="margin: 10px 0 0; color: #c7d2fe; font-size: 14px;">Find your project partner. Build something together.</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 24px; font-weight: 600;">Verify Your Email Address</h2>
                            <p style="margin: 0 0 30px; color: #6b7280; font-size: 16px; line-height: 1.6;">
                                Thank you for signing up! Please verify your email address using one of the methods below.
                            </p>
                            
                            <!-- OTP Section -->
                            <div style="background-color: #f3f4f6; border-radius: 8px; padding: 30px; text-align: center; margin-bottom: 30px;">
                                <p style="margin: 0 0 15px; color: #374151; font-size: 14px; font-weight: 500;">Your Verification Code</p>
                                <div style="font-size: 36px; font-weight: 700; letter-spacing: 8px; color: #4f46e5; font-family: 'Courier New', monospace;">
                                    {otp}
                                </div>
                                <p style="margin: 15px 0 0; color: #9ca3af; font-size: 12px;">
                                    This code expires in {otp_expiry_minutes} minutes
                                </p>
                            </div>
                            
                            <!-- Divider -->
                            <div style="text-align: center; margin: 30px 0;">
                                <span style="display: inline-block; padding: 0 15px; background-color: #ffffff; color: #9ca3af; font-size: 14px;">OR</span>
                                <hr style="margin-top: -10px; border: none; border-top: 1px solid #e5e7eb;">
                            </div>
                            
                            <!-- Link Button -->
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{verification_link}" 
                                   style="display: inline-block; padding: 16px 40px; background-color: #4f46e5; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px; transition: background-color 0.2s;">
                                    Verify via Secure Link
                                </a>
                                <p style="margin: 15px 0 0; color: #9ca3af; font-size: 12px;">
                                    This link expires in {link_expiry_minutes} minutes
                                </p>
                            </div>
                            
                            <!-- Security Notice -->
                            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-top: 30px; border-radius: 0 8px 8px 0;">
                                <p style="margin: 0; color: #92400e; font-size: 14px;">
                                    <strong>Security Notice:</strong> If you didn't create an account with Collabers, please ignore this email. Never share your verification code with anyone.
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #f9fafb; border-radius: 0 0 8px 8px; text-align: center;">
                            <p style="margin: 0 0 10px; color: #6b7280; font-size: 14px;">
                                Need help? Contact us at support@collabers.com
                            </p>
                            <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                                &copy; 2024 Collabers. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def get_verification_email_text(
    otp: str,
    verification_link: str,
    otp_expiry_minutes: int = 5,
    link_expiry_minutes: int = 30
) -> str:
    """Plain text version of the verification email."""
    return f"""
Collabers - Verify Your Email Address

Thank you for signing up! Please verify your email address using one of the methods below.

VERIFICATION CODE
-----------------
Your code: {otp}
This code expires in {otp_expiry_minutes} minutes.

OR

VERIFY VIA LINK
---------------
Click here: {verification_link}
This link expires in {link_expiry_minutes} minutes.

SECURITY NOTICE
---------------
If you didn't create an account with Collabers, please ignore this email.
Never share your verification code with anyone.

---
Need help? Contact us at support@collabers.com
© 2024 Collabers. All rights reserved.
"""


async def send_verification_email(
    to_email: str,
    otp: str,
    link_token: str
) -> bool:
    """Send verification email with OTP and link."""
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP not configured. Email sending disabled.")
        # In development, log that verification would be sent (but not the actual codes!)
        logger.info(f"[DEV] Verification email would be sent to {mask_email(to_email)}")
        return False
    
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={link_token}"
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Verify Your Email - Collabers'
        msg['From'] = settings.SMTP_FROM_EMAIL
        msg['To'] = to_email
        
        # Attach plain text and HTML versions
        text_part = MIMEText(
            get_verification_email_text(otp, verification_link), 
            'plain'
        )
        html_part = MIMEText(
            get_verification_email_html(otp, verification_link), 
            'html'
        )
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send via SMTP with TLS
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Verification email sent to {mask_email(to_email)}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed. Check SMTP_USER and SMTP_PASSWORD.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email: {type(e).__name__}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email: {type(e).__name__}")
        return False


async def send_password_reset_email(
    to_email: str,
    otp: str,
    link_token: str
) -> bool:
    """
    Send password reset email with OTP and reset link.
    Similar to verification email but with different messaging.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP not configured. Email sending disabled.")
        logger.info(f"[DEV] Password reset email would be sent to {mask_email(to_email)}")
        return False
    
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={link_token}"
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password - Collabers</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; max-width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background-color: #4f46e5; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">Collabers</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 24px;">Reset Your Password</h2>
                            <p style="margin: 0 0 30px; color: #6b7280; font-size: 16px; line-height: 1.6;">
                                We received a request to reset your password. Use one of the methods below.
                            </p>
                            
                            <div style="background-color: #f3f4f6; border-radius: 8px; padding: 30px; text-align: center; margin-bottom: 30px;">
                                <p style="margin: 0 0 15px; color: #374151; font-size: 14px; font-weight: 500;">Your Reset Code</p>
                                <div style="font-size: 36px; font-weight: 700; letter-spacing: 8px; color: #4f46e5; font-family: 'Courier New', monospace;">
                                    {otp}
                                </div>
                                <p style="margin: 15px 0 0; color: #9ca3af; font-size: 12px;">This code expires in 5 minutes</p>
                            </div>
                            
                            <div style="text-align: center; margin: 30px 0;">
                                <span style="display: inline-block; padding: 0 15px; background-color: #ffffff; color: #9ca3af; font-size: 14px;">OR</span>
                                <hr style="margin-top: -10px; border: none; border-top: 1px solid #e5e7eb;">
                            </div>
                            
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{reset_link}" style="display: inline-block; padding: 16px 40px; background-color: #4f46e5; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px;">
                                    Reset via Secure Link
                                </a>
                                <p style="margin: 15px 0 0; color: #9ca3af; font-size: 12px;">This link expires in 30 minutes</p>
                            </div>
                            
                            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-top: 30px; border-radius: 0 8px 8px 0;">
                                <p style="margin: 0; color: #92400e; font-size: 14px;">
                                    <strong>Security Notice:</strong> If you didn't request a password reset, please ignore this email and ensure your account is secure.
                                </p>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px 40px; background-color: #f9fafb; border-radius: 0 0 8px 8px; text-align: center;">
                            <p style="margin: 0; color: #9ca3af; font-size: 12px;">&copy; 2024 Collabers. All rights reserved.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Reset Your Password - Collabers'
        msg['From'] = settings.SMTP_FROM_EMAIL
        msg['To'] = to_email
        
        msg.attach(MIMEText(f"Your password reset code is: {otp}\n\nOr click: {reset_link}", 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Password reset email sent to {mask_email(to_email)}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending password reset email: {type(e).__name__}")
        return False
