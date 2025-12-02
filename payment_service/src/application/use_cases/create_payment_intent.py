import uuid
from datetime import datetime
from src.domain.entities.payment import Payment
from src.domain.repositories.payment_repository import PaymentRepository
from src.infrastructure.payment_gateway.mercadopago_client import MercadoPagoClient
from src.infrastructure.config.settings import APP_CREATION_PRICE_MXN

class CreatePaymentIntentUseCase:
    def __init__(self, payment_repo: PaymentRepository, mp_client: MercadoPagoClient):
        self.payment_repo = payment_repo
        self.mp_client = mp_client

    def execute(self, application_id: str, company_id: str, email: str, success_url: str, cancel_url: str) -> dict:
        # 1. Verificar si ya existe pago completado
        existing_payment = self.payment_repo.get_by_application_id(application_id)
        if existing_payment and existing_payment.status == 'completed':
            raise ValueError("Esta aplicación ya ha sido pagada")

        # 2. Crear Preferencia en MercadoPago
        preference_data = self.mp_client.create_preference(
            application_id=application_id,
            company_id=company_id,
            email=email,
            success_url=success_url,
            failure_url=cancel_url
        )

        # 3. Guardar/Actualizar en BD local
        if existing_payment:
            existing_payment.external_id = preference_data['id']
            existing_payment.status = 'pending'
            existing_payment.updated_at = datetime.utcnow()
            self.payment_repo.update(existing_payment)
        else:
            payment = Payment(
                id=None,
                company_id=uuid.UUID(company_id),
                application_id=uuid.UUID(application_id),
                amount=float(APP_CREATION_PRICE_MXN),
                currency="MXN",
                status="pending",
                external_id=preference_data['id'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.payment_repo.create(payment)

        return {'payment_url': preference_data['url']}