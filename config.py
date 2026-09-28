from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Development defaults let the frontend run before PostgreSQL and S3 are
    # configured. Override these values through .env in deployed environments.
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5434/t0_d0"

    secret_key: SecretStr = SecretStr(
        "development-only-change-me-32-bytes-minimum"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    environment: str = "development"


    s3_bucket_name: str = "development-bucket"
    s3_region: str = "us-east-1"
    s3_access_key_id: SecretStr | None = None
    s3_secret_access_key: SecretStr | None = None
    s3_endpoint_url: str | None = None

    max_upload_size_bytes: int = 5 * 1024 * 1024

    posts_per_page: int = 10

    reset_token_expire_minutes: int = 60

    mail_server: str = "localhost"
    mail_port: int = 587
    mail_username: str = ""
    mail_password: SecretStr = SecretStr("")
    mail_from: str = "noreply@example.com"
    mail_use_tls: bool = True

    frontend_url: str = "http://localhost:8000"


settings = Settings()  # type: ignore[call-arg] # Loaded from .env file
