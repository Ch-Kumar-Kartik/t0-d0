from datetime import timedelta, UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from PIL import UnidentifiedImageError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool

from sqlalchemy import delete as sql_delete

import models
# from auth import (
#     CurrentUser,
#     create_access_token,
#     hash_password,
#     verify_password,
#     generate_reset_token,
#     hash_reset_token
# )
# from config import settings
# from database import get_db
# from email_utils import send_password_reset_email
# from image_utils import delete_profile_image, process_profile_image, upload_profile_image
# from schemas import (
#     PaginatedPostsResponse,
#     PostResponse,
#     Token,
#     UserCreate,
#     UserPrivate,
#     UserPublic,
#     UserUpdate,
#     ChangePasswordRequest,
#     ForgotPasswordRequest,
#     ResetPasswordRequest
# )

from botocore.exceptions import ClientError

router = APIRouter()


@router.post("")
async def create_user():
    pass


@router.post("/token")
async def login_for_access_token():
    pass


@router.get("/me")
async def get_current_user():
    pass


@router.post("/forgot-password")
async def forgot_password():
    pass

@router.post("/reset-password")
async def reset_password():
    pass

@router.patch("/me/password")
async def change_password():
    pass

@router.get("/{user_id}")
async def get_user():
    pass


@router.get("/{user_id}/posts")
async def get_user_posts():
    pass

@router.patch("/{user_id}")
async def update_user():
    pass


@router.delete("/{user_id}")
async def delete_user():
    pass


@router.patch("/{user_id}/picture")
async def upload_profile_picture():
    pass


@router.delete("/{user_id}/picture")
async def delete_user_picture():
    pass