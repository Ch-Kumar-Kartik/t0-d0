# t0-d0

A small full-stack to-do application built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, and a vanilla JavaScript/CSS frontend.

## Current features

- User registration and bearer-token login
- Password hashing with Argon2 through `pwdlib`
- Authenticated user profile and account settings
- Username and email updates
- Password change and password reset flows
- Account deletion and logout
- Local profile-picture uploads with a default-image fallback
- Database-backed todos with ownership checks
- Create, list, complete, edit, and delete todo items
- Light and dark themes using CSS
- PostgreSQL development database running in Docker
- Alembic database migrations



## Project structure

```text
.
├── main.py                 # FastAPI application and HTML page routes
├── models.py               # SQLAlchemy database models
├── schemas.py              # Pydantic request and response schemas
├── database.py             # Async SQLAlchemy engine and sessions
├── auth.py                 # Password hashing, JWTs, and current-user dependency
├── config.py               # Environment-backed application settings
├── routers/
│   ├── users.py            # Registration, authentication, account routes
│   └── todos.py            # User-owned todo routes
├── templates/              # Jinja HTML pages
├── static/css/             # Stylesheets
├── static/js/              # Frontend API and page modules
├── static/profile_picture/ # Default profile image
├── static/uploads/         # Local development uploads
└── alembic/                # Database migration history
```



## Requirements

- Python 3.12 or newer
- `uv`
- Docker and Docker Compose



## Local setup

Arch Linux and other PEP 668-managed systems should use a project environment instead of installing packages into system Python.

Install dependencies:

```bash
uv sync
```

Start PostgreSQL:

```bash
docker compose up -d postgres
```

The development database is available at `localhost:5434` with these defaults:

```text
Database: t0_d0
Username: postgres
Password: postgres
```

Apply migrations:

```bash
uv run alembic upgrade head
```

Start the development server:

```bash
uv run fastapi dev main.py
```

Open [http://localhost:8000](http://localhost:8000).

Useful URLs:

- `/` or `/todos` - todo dashboard
- `/login` - login page
- `/register` - registration page
- `/account` - account settings
- `/forgot-password` - request a password reset
- `/reset-password?token=...` - choose a new password
- `/health` - database health check
- `/docs` - interactive OpenAPI documentation



## Environment configuration

Development defaults are defined in `config.py`. For local overrides, create a `.env` file and set values such as:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5434/t0_d0
SECRET_KEY=replace-this-with-a-long-random-secret
ENVIRONMENT=development
FRONTEND_URL=http://localhost:8000
```

Do not commit `.env`, production secrets, or uploaded user files.

## Database migrations

Create a migration after changing a SQLAlchemy model:

```bash
uv run alembic revision --autogenerate -m "describe the change"
```

Review the generated migration before applying it:

```bash
uv run alembic upgrade head
```

Check the current migration:

```bash
uv run alembic current
```



## API overview

Authentication uses a bearer token stored by the current browser frontend.


| Method   | Endpoint                        | Purpose                       |
| -------- | ------------------------------- | ----------------------------- |
| `POST`   | `/api/users`                    | Register a user               |
| `POST`   | `/api/users/token`              | Log in                        |
| `GET`    | `/api/users/me`                 | Read the current user         |
| `PATCH`  | `/api/users/me`                 | Update username or email      |
| `PATCH`  | `/api/users/me/password`        | Change password               |
| `POST`   | `/api/users/forgot-password`    | Create a reset request        |
| `POST`   | `/api/users/reset-password`     | Reset password with a token   |
| `POST`   | `/api/users/me/profile-picture` | Upload a profile picture      |
| `DELETE` | `/api/users/me`                 | Delete the current account    |
| `GET`    | `/api/todos`                    | List the current user’s todos |
| `POST`   | `/api/todos`                    | Create a todo                 |
| `GET`    | `/api/todos/{todo_id}`          | Read one owned todo           |
| `PUT`    | `/api/todos/{todo_id}`          | Replace an owned todo         |
| `PATCH`  | `/api/todos/{todo_id}`          | Update an owned todo          |
| `DELETE` | `/api/todos/{todo_id}`          | Delete an owned todo          |


Every todo read and write is filtered by the authenticated user ID.

## Development notes

Password-reset links are logged by the application in development because email delivery is not configured yet. Profile pictures are stored locally under `static/uploads/profile_pictures/`; that directory is ignored by Git.

Before production, change the development secrets, configure a real email provider, use secure token storage, and move uploaded files to durable object storage.

## Future goals



### Email delivery

- Send password-reset links through an email provider.
- Add email verification and account-notification emails.



### S3 or object storage

- Replace local profile-picture storage with S3-compatible object storage.
- Keep storing only the resulting image URL in `users.profile_image_url`.



### Authorization and RBAC

- Support user and admin roles.
- Restrict admin-only routes.
- Add admin user-management endpoints.
- Preserve todo ownership checks for every role.



### Testing and security hardening

- Test registration and login.
- Test unauthorized requests and expired tokens.
- Test todo ownership boundaries.
- Test password changes, password resets, and account deletion.
- Test invalid, oversized, and fake image uploads.
- Test admin-only routes after RBAC is added.
- Add rate limiting, stronger production headers, and audit logging.



### Product improvements

- Add todo categories, due dates, priorities, and search.
- Replace prompt-based todo editing with an in-page form.
- Add pagination controls and a richer dashboard.
- Add server-side session or secure HTTP-only cookie authentication.

