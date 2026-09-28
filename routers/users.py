import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import models
from auth import (
    CurrentUser,
    create_access_token,
    generate_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
)
from config import settings
from database import get_db
from schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserPrivate,
    UserUpdate,
)


router = APIRouter()
DbSession = Annotated[AsyncSession, Depends(get_db)]
logger = logging.getLogger(__name__)


@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: DbSession) -> models.User:
    username = user.username.strip()
    email = user.email.lower()

    existing_user = await db.scalar(
        select(models.User).where(
            or_(
                func.lower(models.User.username) == username.lower(),
                func.lower(models.User.email) == email,
            )
        )
    )
    if existing_user:
        detail = (
            "Username already exists"
            if existing_user.username.lower() == username.lower()
            else "Email already exists"
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    new_user = models.User(
        username=username,
        email=email,
        password_hash=hash_password(user.password),
    )
    db.add(new_user)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )

    await db.refresh(new_user)
    return new_user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> Token:
    user = await db.scalar(
        select(models.User).where(
            func.lower(models.User.email) == form_data.username.lower()
        )
    )

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return Token(access_token=token)


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(payload: ForgotPasswordRequest, db: DbSession) -> dict[str, str]:
    """Create an expiring password-reset token without disclosing account existence."""
    email = payload.email.lower()
    user = await db.scalar(
        select(models.User).where(func.lower(models.User.email) == email)
    )

    if user:
        raw_token = generate_reset_token()
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.reset_token_expire_minutes
        )

        await db.execute(
            delete(models.PasswordResetToken).where(
                models.PasswordResetToken.user_id == user.id
            )
        )
        db.add(
            models.PasswordResetToken(
                user_id=user.id,
                token_hash=hash_reset_token(raw_token),
                expires_at=expires_at,
            )
        )
        await db.commit()

        if settings.environment.lower() == "development":
            reset_url = (
                f"{settings.frontend_url.rstrip('/')}/reset-password?token={raw_token}"
            )
            logger.info("Development password reset URL for %s: %s", email, reset_url)

    return {"detail": "If an account exists, a password reset request was accepted."}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(payload: ResetPasswordRequest, db: DbSession) -> Response:
    token_record = await db.scalar(
        select(models.PasswordResetToken).where(
            models.PasswordResetToken.token_hash == hash_reset_token(payload.token),
            models.PasswordResetToken.expires_at > datetime.now(UTC),
        )
    )
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    user = await db.get(models.User, token_record.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    user.password_hash = hash_password(payload.new_password)
    await db.execute(
        delete(models.PasswordResetToken).where(
            models.PasswordResetToken.user_id == user.id
        )
    )
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserPrivate)
async def read_current_user(user: CurrentUser) -> models.User:
    return user


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    user.password_hash = hash_password(payload.new_password)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout")
async def logout() -> dict[str, str]:
    """Confirm logout for a stateless bearer-token client.

    The browser removes the token from local storage. Server-side token
    revocation can be added later if immediate invalidation is required.
    """
    return {"detail": "Logged out"}


@router.patch("/me", response_model=UserPrivate)
async def update_current_user(
    updates: UserUpdate,
    user: CurrentUser,
    db: DbSession,
) -> models.User:
    changes = updates.model_dump(exclude_unset=True, exclude_none=True)
    if not changes:
        return user

    if "username" in changes:
        changes["username"] = changes["username"].strip()
        existing_user = await db.scalar(
            select(models.User).where(
                func.lower(models.User.username) == changes["username"].lower(),
                models.User.id != user.id,
            )
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )

    if "email" in changes:
        changes["email"] = changes["email"].lower()
        existing_user = await db.scalar(
            select(models.User).where(
                func.lower(models.User.email) == changes["email"],
                models.User.id != user.id,
            )
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

    for field, value in changes.items():
        setattr(user, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )

    await db.refresh(user)
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(user: CurrentUser, db: DbSession) -> Response:
    await db.delete(user)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
