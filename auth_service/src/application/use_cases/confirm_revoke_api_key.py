from src.domain.repositories.api_key_repository import ApiKeyRepository
from src.domain.repositories.application_repository import ApplicationRepository
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.repositories.revocation_api_key_repository import RevocationApiKeyRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient


class ConfirmRevokeApiKeyUseCase:
    def __init__(self, api_key_repo: ApiKeyRepository, application_repo: ApplicationRepository,
                 company_repo: CompanyRepository, revocation_api_key_repo: RevocationApiKeyRepository,
                 rabbitmq_client: RabbitMQClient):
        self.api_key_repo = api_key_repo
        self.application_repo = application_repo
        self.company_repo = company_repo
        self.revocation_api_key_repo = revocation_api_key_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, api_key_id: str, confirmation_code: str) -> dict:

        revocation_api_key = self.revocation_api_key_repo.get_by_code(confirmation_code)

        if not revocation_api_key:
            raise ValueError("Codigo de confirmacion invalido")

        if str(revocation_api_key.api_key_id) != api_key_id:
            raise ValueError("Codigo no corresponde a esta API key")

        if revocation_api_key.is_used:
            raise ValueError("Codigo ya fue utilizado")

        if revocation_api_key.is_expired():
            raise ValueError("Codigo de confirmacion expirado")


        api_key = self.api_key_repo.get_by_id(api_key_id)
        if not api_key:
            raise ValueError("API key no existe")

        application = self.application_repo.get_by_id(str(api_key.application_id))
        if not application:
            raise ValueError("Aplicación asociada no encontrada")

        company = self.company_repo.get_by_id(str(api_key.company_id))


        api_key.revoke()
        self.api_key_repo.update(api_key)


        application.deactivate()
        self.application_repo.update(application)


        revocation_api_key.mark_as_used()
        self.revocation_api_key_repo.update(revocation_api_key)
        self.revocation_api_key_repo.delete_expired()



        self._send_revocation_email(company, application)

        return {'success': True, 'message': 'API key revocada y aplicación deshabilitada.'}

    def _send_revocation_email(self, company, application):
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h1>Aplicación Deshabilitada</h1>
            <p>Se ha confirmado la revocación de la API Key para la aplicación: <strong>{application.name}</strong>.</p>
            <p style="color: red;">La aplicación ha sido deshabilitada por completo.</p>
            <p>Si deseas volver a usarla, deberás contactar a soporte o reactivarla manualmente (si está disponible).</p>
          </body>
        </html>
        """

        self.rabbitmq_client.publish('emails', {
            'to_email': company.email,
            'subject': 'API Key revocada - Aplicación Detenida',
            'html_body': html_body
        })