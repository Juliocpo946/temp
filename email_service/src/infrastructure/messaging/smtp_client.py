import aiosmtplib
from email.message import EmailMessage
from src.infrastructure.config.settings import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    SMTP_FROM_EMAIL, SMTP_FROM_NAME
)


class SMTPClient:
    def __init__(self):
        self.host = SMTP_HOST
        self.port = SMTP_PORT
        self.user = SMTP_USER
        self.password = SMTP_PASSWORD
        self.from_email = SMTP_FROM_EMAIL
        self.from_name = SMTP_FROM_NAME


    async def send_email(self, to_email: str, subject: str, html_body: str):
        message = EmailMessage()
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = to_email
        message["Subject"] = subject


        message.set_content(html_body, subtype="html")

        try:
            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                use_tls=True,  # Correcto para puerto 465
                start_tls=False
            )
            print(f"[SMTP] Correo enviado a {to_email}")
            return True
        except Exception as e:
            print(f"[SMTP] Error enviando correo: {e}")
            return False