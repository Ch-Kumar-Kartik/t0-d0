from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

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


@router.post("", status_code=HTTP_200_OK, response_model=TodoResponse)
async def create_post(db: Annotated[AsyncSession, Depends(get_db)], todo: TodoCreate):
    new_post = models.Todo(id = todo.id, title = todo.title, description = todo.description, completed = todo.completed)
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=["author"])
    return new_post


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_post(todo_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Todo).where(models.Todo.id == todo_id))
    existing_todo = result.scalar().first()

    if existing_todo:
        return existing_todo
    raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Post not found")

@router.put("/{todo_id}", response_model=TodoResponse)
async def update_post_full(todo_id: int, db: Annotated[AsyncSession, Depends(get_db)], todo_data: TodoCreate):
    result = db.execute(select(models.Todo).where(models.Todo.id == todo_id))
    existing_todo = result.scalar().first()
    if not existing_todo:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Todo to be updated not found")

    existing_todo.title = todo_data.title if todo_data.title else existing_todo.title
    existing_todo.description = todo_data.description if todo_data.description else existing_todo.description
    existing_todo.completed = False

    await db.commit()
    await db.refresh(existing_todo)
    return existing_todo


@router.patch("/{todo_id}", response_model=TodoResponse)
async def update_todo_partial(todo_id: int, todo_data: TodoUpdate, db: Annotated[AsyncSession, Depends(get_db)], current_user):
    result = await db.execute(select(models.Todo).where(models.Todo.id == todo_id))
    todo = result.scalars().first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    if todo.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this todo",
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
