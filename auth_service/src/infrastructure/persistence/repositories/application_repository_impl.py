from typing import Optional, List
from sqlalchemy.orm import Session
import uuid
from src.domain.entities.application import Application
from src.domain.repositories.application_repository import ApplicationRepository
from src.infrastructure.persistence.models.application_model import ApplicationModel

class ApplicationRepositoryImpl(ApplicationRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, application: Application) -> Application:
        db_application = ApplicationModel(
            company_id=application.company_id,
            name=application.name,
            platform=application.platform,
            environment=application.environment,
            is_active=application.is_active
        )
        self.db.add(db_application)
        self.db.commit()
        self.db.refresh(db_application)
        return self._to_domain(db_application)

    def get_by_id(self, application_id: str) -> Optional[Application]:
        db_application = self.db.query(ApplicationModel).filter(ApplicationModel.id == uuid.UUID(application_id)).first()
        return self._to_domain(db_application) if db_application else None

    def get_by_company_id(self, company_id: str) -> List[Application]:
        db_applications = self.db.query(ApplicationModel).filter(ApplicationModel.company_id == uuid.UUID(company_id)).all()
        return [self._to_domain(app) for app in db_applications]

    def update(self, application: Application) -> Application:
        db_application = self.db.query(ApplicationModel).filter(ApplicationModel.id == application.id).first()
        if db_application:
            db_application.name = application.name
            db_application.platform = application.platform
            db_application.environment = application.environment
            db_application.is_active = application.is_active
            self.db.commit()
            self.db.refresh(db_application)
            return self._to_domain(db_application)
        return application

    def delete(self, application_id: str) -> bool:
        db_application = self.db.query(ApplicationModel).filter(ApplicationModel.id == uuid.UUID(application_id)).first()
        if db_application:
            self.db.delete(db_application)
            self.db.commit()
            return True
        return False

    @staticmethod
    def _to_domain(db_application: ApplicationModel) -> Application:
        return Application(
            id=db_application.id,
            company_id=db_application.company_id,
            name=db_application.name,
            platform=db_application.platform.value,
            environment=db_application.environment.value,
            is_active=db_application.is_active,
            created_at=db_application.created_at
        )