from typing import Optional
from sqlalchemy.orm import Session
from src.domain.entities.company import Company
from src.domain.repositories.company_repository import CompanyRepository
from src.infrastructure.persistence.models.company_model import CompanyModel

class CompanyRepositoryImpl(CompanyRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, company: Company) -> Company:
        db_company = CompanyModel(
            name=company.name,
            email=company.email,
            is_active=company.is_active
        )
        self.db.add(db_company)
        self.db.commit()
        self.db.refresh(db_company)
        return self._to_domain(db_company)

    def get_by_id(self, company_id: int) -> Optional[Company]:
        db_company = self.db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
        return self._to_domain(db_company) if db_company else None

    def get_by_email(self, email: str) -> Optional[Company]:
        db_company = self.db.query(CompanyModel).filter(CompanyModel.email == email).first()
        return self._to_domain(db_company) if db_company else None

    def update(self, company: Company) -> Company:
        db_company = self.db.query(CompanyModel).filter(CompanyModel.id == company.id).first()
        if db_company:
            db_company.name = company.name
            db_company.email = company.email
            db_company.is_active = company.is_active
            db_company.updated_at = company.updated_at
            self.db.commit()
            self.db.refresh(db_company)
            return self._to_domain(db_company)
        return company

    def delete(self, company_id: int) -> bool:
        db_company = self.db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
        if db_company:
            self.db.delete(db_company)
            self.db.commit()
            return True
        return False

    @staticmethod
    def _to_domain(db_company: CompanyModel) -> Company:
        return Company(
            id=db_company.id,
            name=db_company.name,
            email=db_company.email,
            is_active=db_company.is_active,
            created_at=db_company.created_at,
            updated_at=db_company.updated_at
        )
