from datetime import datetime
from typing import Optional

class PaymentDTO:
    def __init__(
        self,
        id: str,
        company_id: str,
        application_id: str,
        amount: float,
        currency: str,
        status: str,
        created_at: datetime,
        updated_at: datetime
    ):
        self.id = id
        self.company_id = company_id
        self.application_id = application_id
        self.amount = amount
        self.currency = currency
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "application_id": self.application_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }