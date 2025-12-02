from typing import Optional
from sqlalchemy.orm import Session
import uuid
from src.domain.entities.payment import Payment
from src.domain.repositories.payment_repository import PaymentRepository
from src.infrastructure.persistence.models.payment_model import PaymentModel


class PaymentRepositoryImpl(PaymentRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, payment: Payment) -> Payment:
        db_payment = PaymentModel(
            id=payment.id,
            company_id=payment.company_id,
            application_id=payment.application_id,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            external_id=payment.external_id,
            created_at=payment.created_at,
            updated_at=payment.updated_at
        )
        self.db.add(db_payment)
        self.db.commit()
        self.db.refresh(db_payment)
        return self._to_domain(db_payment)

    def get_by_external_id(self, external_id: str) -> Optional[Payment]:
        db_payment = self.db.query(PaymentModel).filter(PaymentModel.external_id == external_id).first()
        return self._to_domain(db_payment) if db_payment else None

    def get_by_application_id(self, application_id: str) -> Optional[Payment]:
        # Manejar string o UUID
        if isinstance(application_id, str):
            application_id = uuid.UUID(application_id)

        db_payment = self.db.query(PaymentModel).filter(PaymentModel.application_id == application_id).first()
        return self._to_domain(db_payment) if db_payment else None

    def update(self, payment: Payment) -> Payment:
        db_payment = self.db.query(PaymentModel).filter(PaymentModel.id == payment.id).first()
        if db_payment:
            db_payment.status = payment.status
            db_payment.updated_at = payment.updated_at
            self.db.commit()
            self.db.refresh(db_payment)
            return self._to_domain(db_payment)
        return payment

    @staticmethod
    def _to_domain(db_payment: PaymentModel) -> Payment:
        return Payment(
            id=db_payment.id,
            company_id=db_payment.company_id,
            application_id=db_payment.application_id,
            amount=db_payment.amount,
            currency=db_payment.currency,
            status=db_payment.status,
            external_id=db_payment.external_id,
            created_at=db_payment.created_at,
            updated_at=db_payment.updated_at
        )