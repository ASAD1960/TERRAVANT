from unittest.mock import MagicMock

from app.core.config import get_settings
from app.services import email as email_service


def test_password_reset_email_uses_tls_and_sends_message(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "test-user")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "test-password")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@example.com")
    monkeypatch.setattr(settings, "SMTP_USE_TLS", True)
    monkeypatch.setattr(settings, "SMTP_TIMEOUT_S", 10.0)
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://terravant.example.com")
    monkeypatch.setattr(settings, "RESET_TOKEN_MINUTES", 30)

    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    monkeypatch.setattr(email_service.smtplib, "SMTP", MagicMock(return_value=smtp))

    email_service.send_password_reset_email(
        "farmer@example.com",
        "test-token/with+symbols",
    )

    email_service.smtplib.SMTP.assert_called_once_with(
        "smtp.example.com",
        587,
        timeout=10.0,
    )
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with("test-user", "test-password")
    smtp.send_message.assert_called_once()

    message = smtp.send_message.call_args.args[0]
    assert message["To"] == "farmer@example.com"
    assert message["From"] == "noreply@example.com"
    assert message["Subject"] == "Reset your TERRAVANT password"

    body = message.get_content()
    assert "test-token%2Fwith%2Bsymbols" in body
    assert "30 minutes" in body
    assert "https://terravant.example.com/reset-password?" in body


def test_smtp_is_configured_requires_all_credentials(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_USERNAME", "test-user")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", None)
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@example.com")

    assert email_service.smtp_is_configured() is False
