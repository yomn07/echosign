import os
import secrets
from datetime import datetime, timedelta, timezone
import hashlib

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
import models, schemas, security
from email_service import (
    send_verification_email,
    send_password_reset_email,
)
router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

 

@router.post(
    "/register",
    response_model=schemas.MessageResponse
)
def register(
    user: schemas.UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):

    # Check if email already exists
    existing_user = (
        db.query(models.User)
        .filter(models.User.email == user.email)
        .first()
    )

    if existing_user:

        # If already verified
        if existing_user.is_verified:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        verification_token = (
            security.create_email_verification_token(
                existing_user.email
            )
        )

        existing_user.verification_token = (
            verification_token
        )

        existing_user.verification_expires_at = (
            datetime.now(timezone.utc)
            + timedelta(minutes=30)
        )

        db.commit()

        frontend_url = os.getenv(
            "FRONTEND_URL",
            "http://localhost:8000"
        )

        verification_link = (
            f"{frontend_url}/verify-email"
            f"?token={verification_token}"
        )

        background_tasks.add_task(
            send_verification_email,
            existing_user.email,
            existing_user.first_name,
            verification_link
        )

        return {
            "message": "A new verification email has been sent."
        }

    verification_token = (
        security.create_email_verification_token(
            user.email
        )
    )

    verification_expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=30)
    )

    new_user = models.User(

        first_name=user.first_name,

        last_name=user.last_name,

        email=user.email,

        hashed_password=security.hash_password(
            user.password
        ),

        role=user.role,

        is_verified=False,

        verification_token=verification_token,

        verification_expires_at=verification_expires_at
    )

    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    frontend_url = os.getenv(
        "FRONTEND_URL",
        "http://localhost:8000"
    )

    verification_link = (
        f"{frontend_url}/verify-email"
        f"?token={verification_token}"
    )

    # Send email in background
    background_tasks.add_task(
        send_verification_email,
        new_user.email,
        new_user.first_name,
        verification_link
    )

    return {
        "message": (
            "Account created. "
            "Please check your email to verify your account."
        )
    }



@router.get(
    "/verify-email",
    response_model=schemas.MessageResponse
)
def verify_email(
    token: str,
    db: Session = Depends(get_db)
):

    # Decode JWT
    email = (
        security.verify_email_verification_token(
            token
        )
    )

    if not email:

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification link"
        )

    # Find user
    user = (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.is_verified:

        return {
            "message": "Email already verified."
        }

    if user.verification_token != token:

        raise HTTPException(
            status_code=400,
            detail="Invalid verification token"
        )

    if (
        not user.verification_expires_at
        or user.verification_expires_at
        < datetime.now(timezone.utc)
    ):

        raise HTTPException(
            status_code=400,
            detail="Verification link has expired"
        )

    # Verify account
    user.is_verified = True

    user.verification_token = None

    user.verification_expires_at = None

    db.commit()

    return {
        "message": "Email verified successfully."
    }


@router.post(
    "/signin",
    response_model=schemas.TokenResponse
)
def signin(
    credentials: schemas.Usersignin,
    db: Session = Depends(get_db)
):

    user = (
        db.query(models.User)
        .filter(
            models.User.email == credentials.email
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    if not user.is_verified:

        raise HTTPException(
            status_code=403,
            detail="Please verify your email before signing in"
        )

    # Check password
    if not security.verify_password(
        credentials.password,
        user.hashed_password
    ):

        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    token = security.create_access_token(
        {
            "sub": str(user.id),
            "email": user.email
        }
    )

    return {

        "access_token": token,

        "token_type": "bearer",

        "user": {

            "id": user.id,

            "first_name": user.first_name,

            "last_name": user.last_name,

            "email": user.email,

            "role": user.role,

            "is_verified": user.is_verified
        }
    }


@router.post(
    "/forgot-password",
    response_model=schemas.MessageResponse
)
def forgot_password(
    request: schemas.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):

    user = (
        db.query(models.User)
        .filter(
            models.User.email == request.email
        )
        .first()
    )

    if not user:
        return {
            "message": (
                "If an account exists with that email, "
                "a password reset link has been sent."
            )
        }

    reset_token = secrets.token_urlsafe(32)

    reset_token_hash = hashlib.sha256(
        reset_token.encode()
    ).hexdigest()

    user.reset_token_hash = reset_token_hash

    user.reset_token_expires = (
        datetime.now(timezone.utc)
        + timedelta(minutes=30)
    )

    db.commit()

    # Frontend URL
    frontend_url = os.getenv(
        "FRONTEND_URL",
        "http://localhost:8000"
    )

    # Create password reset link
    reset_link = (
        f"{frontend_url}/reset-password"
        f"?token={reset_token}"
    )

    # Send reset email in background
    background_tasks.add_task(
        send_password_reset_email,
        user.email,
        user.first_name,
        reset_link
    )

    return {
        "message": (
            "If an account exists with that email, "
            "a password reset link has been sent."
        )
    }


# ============================================================
# RESET PASSWORD
# ============================================================

@router.post(
    "/reset-password",
    response_model=schemas.MessageResponse
)
def reset_password(
    request: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db)
):

    # Hash token received from frontend
    token_hash = hashlib.sha256(
        request.token.encode()
    ).hexdigest()

    # Find user using hashed token
    user = (
        db.query(models.User)
        .filter(
            models.User.reset_token_hash == token_hash
        )
        .first()
    )

    # Invalid token
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired password reset link"
        )

    # Check expiration
    if (
        not user.reset_token_expires
        or user.reset_token_expires
        < datetime.now(timezone.utc)
    ):

        # Remove expired token
        user.reset_token_hash = None
        user.reset_token_expires = None

        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Password reset link has expired"
        )

    # Update password
    user.hashed_password = security.hash_password(
        request.new_password
    )

    # Invalidate reset token
    user.reset_token_hash = None
    user.reset_token_expires = None

    db.commit()

    return {
        "message": "Password reset successfully."
    }    