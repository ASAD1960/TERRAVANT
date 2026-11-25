import pytest
from pydantic import ValidationError

from app.core.config import REPO_ROOT, Settings

PRODUCTION_SETTINGS = {
    "DATABASE_URL": "postgresql+psycopg2://user:password@localhost/terravant",
    "CORS_ORIGINS": ["https://terravant.example.com"],
    "REDIS_URL": "redis://localhost:6379/0",
    "SMTP_HOST": "smtp.example.com",
    "SMTP_PORT": 587,
    "SMTP_USERNAME": "test-user",
    "SMTP_PASSWORD": "test-password",
    "SMTP_FROM_EMAIL": "noreply@example.com",
    "SMTP_USE_TLS": True,
    "FRONTEND_URL": "https://terravant.example.com",
}


def test_environment_is_normalized():
    settings = Settings(
        _env_file=None,
        ENV="PRODUCTION",
        SECRET_KEY="aB3dEf6hJk9mNp2qRs5uVw8xYz1AbCdEfGhIjKlMnOpQrStU",
        **PRODUCTION_SETTINGS,
    )
    assert settings.ENV == "production"
    assert settings.is_prod is True


def test_dev_environment_alias_is_supported():
    settings = Settings(_env_file=None, ENV=" DEV ")
    assert settings.ENV == "development"
    assert settings.is_prod is False


def test_production_accepts_strong_secret():
    settings = Settings(
        _env_file=None,
        ENV="production",
        SECRET_KEY="aB3dEf6hJk9mNp2qRs5uVw8xYz1AbCdEfGhIjKlMnOpQrStU",
        **PRODUCTION_SETTINGS,
    )
    assert settings.ENV == "production"


@pytest.mark.parametrize(
    "secret",
    [
        "short",
        "change-me-in-production-use-a-long-random-string",
        "generate-with-python-token",
        "REPLACE_WITH_A_RANDOM_SECRET",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    ],
)
def test_production_rejects_weak_or_placeholder_secrets(secret):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ENV="production", SECRET_KEY=secret)


def test_development_does_not_require_production_secret():
    settings = Settings(
        _env_file=None,
        ENV="development",
        SECRET_KEY="development-secret",
    )
    assert settings.SECRET_KEY == "development-secret"


def test_env_file_is_resolved_from_repository_root():
    assert Settings.model_config["env_file"] == REPO_ROOT / ".env"

@pytest.mark.parametrize(
    "redis_url",
    [
        "http://localhost:6379",
        "redis://",
        "redis://localhost:abc",
        " redis://localhost:6379/0 ",
    ],
)
def test_invalid_redis_urls_are_rejected(redis_url):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, REDIS_URL=redis_url)


@pytest.mark.parametrize(
    "origin",
    [
        "https://example.com/path",
        "https://example.com?query=1",
        "https://example.com#fragment",
        "http://example.com",
        "*",
    ],
)
def test_invalid_production_cors_origins_are_rejected(origin):
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            ENV="production",
            SECRET_KEY="aB3dEf6hJk9mNp2qRs5uVw8xYz1AbCdEfGhIjKlMnOpQrStU",
            CORS_ORIGINS=[origin],
            **{
                key: value
                for key, value in PRODUCTION_SETTINGS.items()
                if key != "CORS_ORIGINS"
            },
        )

@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql://",
        "postgresql://localhost",
        "postgresql://user:password@/terravant",
        "mysql://user:password@localhost/terravant",
    ],
)
def test_invalid_production_database_urls_are_rejected(database_url):
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            ENV="production",
            SECRET_KEY="aB3dEf6hJk9mNp2qRs5uVw8xYz1AbCdEfGhIjKlMnOpQrStU",
            DATABASE_URL=database_url,
            CORS_ORIGINS=PRODUCTION_SETTINGS["CORS_ORIGINS"],
            REDIS_URL=PRODUCTION_SETTINGS["REDIS_URL"],
        )
