import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

from app.core.config import get_settings


def smtp_is_configured() -> bool:
    settings = get_settings()
    return all((
        settings.SMTP_HOST,
        settings.SMTP_USERNAME,
        settings.SMTP_PASSWORD,
        settings.SMTP_FROM_EMAIL,
    ))


def send_password_reset_email(to_email: str, token: str) -> None:
    settings = get_settings()

    if not smtp_is_configured():
        raise RuntimeError("SMTP is not fully configured")

    reset_url = (
        f"{settings.FRONTEND_URL}/reset-password?"
        f"{urlencode({'token': token})}"
    )

    message = EmailMessage()
    message["Subject"] = "Reset your TERRAVANT password"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email
    message.set_content(
        "We received a request to reset your TERRAVANT password.\n\n"
        f"Use this link to choose a new password:\n{reset_url}\n\n"
        f"This link expires in {settings.RESET_TOKEN_MINUTES} minutes.\n"
        "If you did not request this, you can ignore this email."
    )

    with smtplib.SMTP(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        timeout=settings.SMTP_TIMEOUT_S,
    ) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls(context=ssl.create_default_context())

        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
