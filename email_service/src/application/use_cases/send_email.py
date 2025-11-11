from src.infrastructure.messaging.smtp_client import SMTPClient

class SendEmailUseCase:
    def __init__(self, smtp_client: SMTPClient):
        self.smtp_client = smtp_client

    async def execute(self, to_email: str, subject: str, html_body: str) -> bool:
        result = await self.smtp_client.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body
        )
        
        if result:
            print(f"Email enviado a {to_email} - Asunto: {subject}")
        else:
            print(f"Error al enviar email a {to_email}")
        
        return result