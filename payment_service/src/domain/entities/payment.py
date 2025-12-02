from datetime import datetime
from typing import Optional
import uuid

class Payment:
    def __init__(
        self,
        id: Optional[uuid.UUID],
        company_id: uuid.UUID,
        application_id: uuid.UUID,
        amount: float,
        currency: str,
        status: str,
        external_id: str,
        created_at: datetime,
        updated_at: datetime
    ):
        self.id = id or uuid.uuid4()
        self.company_id = company_id
        self.application_id = application_id
        self.amount = amount
        self.currency = currency
        self.status = status  # 'pending', 'completed', 'failed'
        self.external_id = external_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def complete(self) -> None:
        self.status = "completed"
        self.updated_at = datetime.utcnow()

    def fail(self) -> None:
        self.status = "failed"
        self.updated_at = datetime.utcnow()