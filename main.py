from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ExceptionHandler

import models
from routers import todos
# from config import settings
# from database import engine, get_db
# from routers import posts, users

# @asynccontextmanager
# async def lifespan(_app: FastAPI):
#     yield
#     await engine.dispose()


dummy_users = [
    {
        "user_id": 1,
        "email": "maya@example.com",
        "password": "maya-password",
        "todos": [
            {"todo_id": 1, "title": "Review project requirements", "completed": True},
            {"todo_id": 2, "title": "Build the FastAPI endpoints", "completed": False},
            {"todo_id": 3, "title": "Pick up groceries", "completed": False},
            {"todo_id": 4, "title": "Reply to Maya's email", "completed": True},
            {"todo_id": 5, "title": "Read for 30 minutes", "completed": False},
        ],
    },
    {
        "user_id": 2,
        "email": "alex@example.com",
        "password": "alex-password",
        "todos": [
            {"todo_id": 6, "title": "Plan the week's priorities", "completed": True},
            {"todo_id": 7, "title": "Write the database schema", "completed": False},
            {"todo_id": 8, "title": "Schedule a team check-in", "completed": False},
            {"todo_id": 9, "title": "Organize the workspace", "completed": True},
            {"todo_id": 10, "title": "Go for an evening walk", "completed": False},
        ],
    },
]


# app = FastAPI(lifespan=lifespan)
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    response.headers["X-Content-Type-Options"] = "nosniff"

    if "Referrer-Policy" not in response.headers:
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if request.url.hostname not in ("localhost", "127.0.0.1"):
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )

    return response

# @app.get("/health")
# async def health_check(db: Annotated[AsyncSession, Depends(get_db)]):
#     pass

@app.get("/")
@app.get("/todos")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={},
    )

@app.get("/users/{user_id}/todos")
async def user_todos_page(user_id: int):
    for i in range(len(dummy_users)):
        if dummy_users[i]["user_id"] == user_id:
            return JSONResponse(status_code=200, content=dummy_users[i]["todos"])


@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={},
    )

@app.get("/account")
async def account_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="account.html",
        context={},
    )

@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    if request.url.path.startswith('/api'):
        return JSONResponse(status_code=exception.status_code, content=exception.detail)

    message = (exception.detail or "An error occured, please check your request and try again.")

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: StarletteHTTPException):
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exception)

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )

    


# app.include_router
