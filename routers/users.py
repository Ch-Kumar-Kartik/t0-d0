from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import models
from auth import CurrentUser, create_access_token, hash_password, verify_password
from config import settings
from database import get_db
from schemas import Token, UserCreate, UserPrivate, UserUpdate


router = APIRouter()
DbSession = Annotated[AsyncSession, Depends(get_db)]


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


@router.get("/me", response_model=UserPrivate)
async def read_current_user(user: CurrentUser) -> models.User:
    return user


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
