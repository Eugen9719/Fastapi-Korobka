from backend.app.base.utils.email import send_email

from pathlib import Path

from backend.core.config import settings


def send_reset_password_email(email_to: str, email: str, token: str):
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    with open(Path(settings.EMAIL_TEMPLATE_DIR) / "reset_password.html") as f:
        template_str = f.read()
    if hasattr(token, "decode"):
        use_token = token.decode()
    else:
        use_token = token
    server_host = settings.SERVER_HOST
    link = f"{server_host}/reset-password?token={use_token}"
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


def send_new_account_email(email_to: str, full_name: str, password: str, uuid: str):
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {full_name}"
    with open(Path(settings.EMAIL_TEMPLATE_DIR) / "new_account.html") as f:
        template_str = f.read()

    link = f"{settings.SERVER_HOST}/verify?token={uuid}"
    send_email(
        email_to=email_to,
        subject_template=subject,
        html_template=template_str,
        environment={"project_name": settings.PROJECT_NAME,
                     "full_name": full_name,
                     "password": password,
                     "email": email_to,
                     "link": link
                     }
    )
    return None
