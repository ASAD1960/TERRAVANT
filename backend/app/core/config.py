from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "TERRAVANT"
    ENV: Literal["development", "production", "test"] = "development"
    API_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./terravant.db"
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ACCESS_TOKEN_MINUTES: int = 30
    REFRESH_TOKEN_DAYS: int = 7
    RESET_TOKEN_MINUTES: int = 30

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    UPLOAD_DIR: Path = REPO_ROOT / "backend" / "storage" / "uploads"
    MAX_UPLOAD_MB: int = 8
    MAX_IMAGE_PIXELS: int = 20_000_000
    ML_ARTIFACT_DIR: Path = REPO_ROOT / "ml" / "artifacts"
    DISEASE_CONFIDENCE_THRESHOLD: float = 0.60

    WEATHER_BASE_URL: str = "https://api.open-meteo.com/v1"
    WEATHER_ARCHIVE_URL: str = "https://archive-api.open-meteo.com/v1"
    WEATHER_TIMEOUT_S: float = 6.0
    WEATHER_CACHE_TTL_S: int = 900

    RATE_LIMIT_AUTH_PER_MIN: int = 20
    REDIS_URL: str | None = None

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_USE_TLS: bool = True
    SMTP_TIMEOUT_S: float = 10.0
    FRONTEND_URL: str = "http://localhost:5173"

    @field_validator("ENV", mode="before")
    @classmethod
    def normalize_environment(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized == "dev":
                normalized = "development"
            return normalized
        return value

    @field_validator("API_PREFIX")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith("/") or value == "/":
            raise ValueError("API_PREFIX must start with / and cannot be /")
        return value.rstrip("/")

    @field_validator("ACCESS_TOKEN_MINUTES", "RESET_TOKEN_MINUTES")
    @classmethod
    def validate_token_minutes(cls, value: int) -> int:
        if not 1 <= value <= 1440:
            raise ValueError("Token lifetime must be between 1 and 1440 minutes")
        return value

    @field_validator("REFRESH_TOKEN_DAYS")
    @classmethod
    def validate_refresh_days(cls, value: int) -> int:
        if not 1 <= value <= 365:
            raise ValueError("Refresh token lifetime must be between 1 and 365 days")
        return value

    @field_validator("MAX_UPLOAD_MB")
    @classmethod
    def validate_upload_size(cls, value: int) -> int:
        if not 1 <= value <= 50:
            raise ValueError("MAX_UPLOAD_MB must be between 1 and 50")
        return value

    @field_validator("MAX_IMAGE_PIXELS")
    @classmethod
    def validate_image_pixels(cls, value: int) -> int:
        if not 1 <= value <= 100_000_000:
            raise ValueError("MAX_IMAGE_PIXELS must be between 1 and 100 million")
        return value

    @field_validator("DISEASE_CONFIDENCE_THRESHOLD")
    @classmethod
    def validate_disease_threshold(cls, value: float) -> float:
        if not 0 < value < 1:
            raise ValueError("DISEASE_CONFIDENCE_THRESHOLD must be between 0 and 1")
        return value

    @field_validator("WEATHER_TIMEOUT_S")
    @classmethod
    def validate_weather_timeout(cls, value: float) -> float:
        if not 0.1 <= value <= 120:
            raise ValueError("WEATHER_TIMEOUT_S must be between 0.1 and 120 seconds")
        return value

    @field_validator("WEATHER_CACHE_TTL_S")
    @classmethod
    def validate_weather_cache(cls, value: int) -> int:
        if not 0 <= value <= 86_400:
            raise ValueError("WEATHER_CACHE_TTL_S must be between 0 and 86400")
        return value

    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, value: str | None) -> str | None:
        if value is not None:
            if value != value.strip():
                raise ValueError("REDIS_URL cannot contain surrounding whitespace")

            parsed = urlparse(value)

            try:
                port = parsed.port
            except ValueError as exc:
                raise ValueError("REDIS_URL contains an invalid port") from exc

            if (
                parsed.scheme not in ("redis", "rediss")
                or not parsed.hostname
                or port is None
                or not 1 <= port <= 65535
            ):
                raise ValueError(
                    "REDIS_URL must contain a valid redis:// or rediss:// host and port"
                )

        return value

    @field_validator("SMTP_PORT")
    @classmethod
    def validate_smtp_port(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError("SMTP_PORT must be between 1 and 65535")
        return value

    @field_validator("SMTP_TIMEOUT_S")
    @classmethod
    def validate_smtp_timeout(cls, value: float) -> float:
        if not 0.1 <= value <= 120:
            raise ValueError("SMTP_TIMEOUT_S must be between 0.1 and 120 seconds")
        return value

    @field_validator("SMTP_HOST", "SMTP_USERNAME", "SMTP_FROM_EMAIL")
    @classmethod
    def normalize_smtp_strings(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("SMTP settings cannot be blank")
        return value

    @field_validator("FRONTEND_URL")
    @classmethod
    def validate_frontend_url(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        parsed = urlparse(value)
        if (
            not parsed.scheme
            or not parsed.hostname
            or parsed.path
            or parsed.query
            or parsed.fragment
            or parsed.username
            or parsed.password
        ):
            raise ValueError("FRONTEND_URL must be a valid origin without a path")
        return value

    @field_validator("RATE_LIMIT_AUTH_PER_MIN")
    @classmethod
    def validate_auth_rate_limit(cls, value: int) -> int:
        if not 1 <= value <= 1000:
            raise ValueError("RATE_LIMIT_AUTH_PER_MIN must be between 1 and 1000")
        return value

    @property
    def is_prod(self) -> bool:
        return self.ENV == "production"

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.ENV != "production":
            return self

        secret = self.SECRET_KEY.strip()
        normalized = secret.lower()

        placeholders = (
            "change-me",
            "generate-with-python",
            "replace-with",
            "replace_me",
            "your-secret",
            "example",
            "insert-secret",
        )

        if len(secret) < 32:
            raise ValueError(
                "Production SECRET_KEY must contain at least 32 characters"
            )

        if any(marker in normalized for marker in placeholders):
            raise ValueError(
                "Production SECRET_KEY contains a placeholder value"
            )

        if len(set(secret)) < 12:
            raise ValueError(
                "Production SECRET_KEY does not have sufficient character diversity"
            )

        database = urlparse(self.DATABASE_URL)
        if (
            database.scheme not in ("postgresql", "postgresql+psycopg2")
            or not database.hostname
            or not database.path.strip("/")
            or not database.username
            or not database.password
        ):
            raise ValueError(
                "Production DATABASE_URL must contain valid PostgreSQL credentials, host, and database name"
            )

        if not self.CORS_ORIGINS or "*" in self.CORS_ORIGINS:
            raise ValueError(
                "Production CORS_ORIGINS must contain explicit allowed origins"
            )

        for origin in self.CORS_ORIGINS:
            parsed = urlparse(origin)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.path
                or parsed.query
                or parsed.fragment
                or parsed.username
                or parsed.password
            ):
                raise ValueError(
                    "Production CORS origins must be HTTPS origins without paths or credentials"
                )

        if not self.REDIS_URL:
            raise ValueError("Production REDIS_URL is required")

        if not all((
            self.SMTP_HOST,
            self.SMTP_USERNAME,
            self.SMTP_PASSWORD,
            self.SMTP_FROM_EMAIL,
        )):
            raise ValueError("Production SMTP host, username, password, and sender email are required")

        if not self.SMTP_USE_TLS:
            raise ValueError("Production SMTP_USE_TLS must be enabled")

        frontend = urlparse(self.FRONTEND_URL)
        if (
            frontend.scheme != "https"
            or not frontend.hostname
            or frontend.path
            or frontend.query
            or frontend.fragment
            or frontend.username
            or frontend.password
        ):
            raise ValueError("Production FRONTEND_URL must be an HTTPS origin")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
