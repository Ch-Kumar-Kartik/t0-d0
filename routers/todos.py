from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import models
from auth import CurrentUser
from database import get_db
from schemas import PaginatedTodosResponse, TodoCreate, TodoResponse, TodoUpdate

router = APIRouter()

@router.get("", response_model=PaginatedTodosResponse)
async def get_todos(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedTodosResponse:
    todo_filter = models.Todo.user_id == current_user.id

    total = (
        await db.scalar(
            select(func.count()).select_from(models.Todo).where(todo_filter)
        )
        or 0
    )

    result = await db.execute(
        select(models.Todo)
        .where(todo_filter)
        .order_by(models.Todo.created_at.desc(), models.Todo.id.desc())
        .offset(skip)
        .limit(limit),
    )
    todos = result.scalars().all()

    has_more = skip + len(todos) < total

    return PaginatedTodosResponse(
        todos=[TodoResponse.model_validate(todo) for todo in todos],
        total=total,
        skip=skip,
        limit=limit,
        has_more=has_more,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TodoResponse)
async def create_todo(
    todo: TodoCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> models.Todo:
    new_todo = models.Todo(
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        user_id=current_user.id,
    )
    db.add(new_todo)
    await db.commit()
    await db.refresh(new_todo)
    return new_todo


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> models.Todo:
    todo = await db.scalar(
        select(models.Todo).where(
            models.Todo.id == todo_id,
            models.Todo.user_id == current_user.id,
        )
    )
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo

@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo_full(
    todo_id: int,
    todo_data: TodoCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> models.Todo:
    existing_todo = await db.scalar(
        select(models.Todo).where(
            models.Todo.id == todo_id,
            models.Todo.user_id == current_user.id,
        )
    )
    if not existing_todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    existing_todo.title = todo_data.title
    existing_todo.description = todo_data.description
    existing_todo.completed = todo_data.completed

    await db.commit()
    await db.refresh(existing_todo)
    return existing_todo


@router.patch("/{todo_id}", response_model=TodoResponse)
async def update_todo_partial(
    todo_id: int,
    todo_data: TodoUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> models.Todo:
    todo = await db.scalar(
        select(models.Todo).where(
            models.Todo.id == todo_id,
            models.Todo.user_id == current_user.id,
        )
    )
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    update_data = todo_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)

    await db.commit()
    await db.refresh(todo)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    todo = await db.scalar(
        select(models.Todo).where(
            models.Todo.id == todo_id,
            models.Todo.user_id == current_user.id,
        )
    )
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    await db.delete(todo)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
