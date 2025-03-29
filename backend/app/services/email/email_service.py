import uuid
from pathlib import Path

from backend.app.services.email.email import send_email
from backend.core.config import settings


class EmailService:
    """Сервис отправки email"""

    @staticmethod
    async def send_verification_email(email: str, full_name: str, password: str, link: uuid):
        project_name = settings.PROJECT_NAME
        subject = f"{project_name} - New account for user {full_name}"
        with open(Path(settings.EMAIL_TEMPLATE_DIR) / "new_account.html") as f:
            template_str = f.read()

        link = f"{settings.SERVER_HOST}/verify?token={link}"
        send_email(
            email_to=email,
            subject_template=subject,
            html_template=template_str,
            environment={"project_name": settings.PROJECT_NAME,
                         "full_name": full_name,
                         "password": password,
                         "email": email,
                         "link": link
                         }
        )
        return None


    @staticmethod
    async def send_reset_password(email_to: str, email: str, token: str):
        project_name = settings.PROJECT_NAME
        subject = f"{project_name} - Password recovery for user {email}"
        with open(Path(settings.EMAIL_TEMPLATE_DIR) / "reset_password.html") as f:
            template_str = f.read()
        if hasattr(token, "decode"):
            use_token = token.decode()
        else:
            use_token = token
        server_host = settings.SERVER_HOST
        link = f"{server_host}/api/v1/vendor-profile/reset-password?token={use_token}"
        send_email(
            email_to=email_to,
            subject_template=subject,
            html_template=template_str,
            environment={"project_name": settings.PROJECT_NAME,
                         "username": email,
                         "email": email_to,
                         "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
                         "link": link
                         }
        )

        return None
