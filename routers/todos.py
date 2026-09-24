# from typing import Annotated

# from fastapi import APIRouter, Depends, HTTPException, Query, status
# from sqlalchemy import func, select
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

# import models
# from auth import CurrentUser
# from config import settings
# from database import get_db
# from schemas import PaginatedPostsResponse, PostCreate, PostResponse, PostUpdate

# router = APIRouter()

# @router.get("", response_model=PaginatedPostsResponse)
# async def get_posts():
#     pass


# @router.post()
# async def create_post():
#     pass


# @router.get("/{post_id}")
# async def get_post():
#     pass


# @router.put("/{post_id}")
# async def update_post_full():
#     pass


# @router.patch("/{post_id}")
# async def update_post_partial():
#     pass


# @router.delete("/{post_id}")
# async def delete_post():
#     pass