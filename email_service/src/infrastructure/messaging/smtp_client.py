import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.infrastructure.config.settings import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL, SMTP_FROM_NAME

class SMTPClient:
    def __init__(self):
        self.host = SMTP_HOST
        self.port = SMTP_PORT
        self.user = SMTP_USER
        self.password = SMTP_PASSWORD
        self.from_email = SMTP_FROM_EMAIL
        self.from_name = SMTP_FROM_NAME

    async def send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email

            part = MIMEText(html_body, "html")
            message.attach(part)

            async with aiosmtplib.SMTP(hostname=self.host, port=self.port, use_tls=True) as smtp:
                await smtp.login(self.user, self.password)
                await smtp.sendmail(self.from_email, to_email, message.as_string())
            
            return True
        except Exception as e:
            print(f"Error al enviar email: {str(e)}")
            return False