from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories.content_repository_impl import ContentRepositoryImpl
from src.application.dtos.content_dto import CreateContentDTO, UpdateContentDTO, ContentFilterDTO
from src.application.use_cases.create_content import CreateContentUseCase
from src.application.use_cases.update_content import UpdateContentUseCase
from src.application.use_cases.delete_content import DeleteContentUseCase
from src.application.use_cases.get_content import GetContentUseCase
from src.application.use_cases.list_contents import ListContentsUseCase

router = APIRouter()


@router.post("/", status_code=201)
def create_content(dto: CreateContentDTO, db: Session = Depends(get_db)):
    repository = ContentRepositoryImpl(db)
    use_case = CreateContentUseCase(repository)
    content = use_case.execute(dto)
    return content.to_dict()


@router.get("/")
def list_contents(
    topic: Optional[str] = Query(None),
    subtopic: Optional[str] = Query(None),
    activity_type: Optional[str] = Query(None),
    intervention_type: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    repository = ContentRepositoryImpl(db)
    use_case = ListContentsUseCase(repository)
    filters = ContentFilterDTO(
        topic=topic,
        subtopic=subtopic,
        activity_type=activity_type,
        intervention_type=intervention_type,
        active=active
    )
    contents = use_case.execute(filters)
    return [c.to_dict() for c in contents]


@router.get("/{content_id}")
def get_content(content_id: int, db: Session = Depends(get_db)):
    repository = ContentRepositoryImpl(db)
    use_case = GetContentUseCase(repository)
    content = use_case.execute(content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    return content.to_dict()


@router.put("/{content_id}")
def update_content(content_id: int, dto: UpdateContentDTO, db: Session = Depends(get_db)):
    repository = ContentRepositoryImpl(db)
    use_case = UpdateContentUseCase(repository)
    content = use_case.execute(content_id, dto)
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    return content.to_dict()


@router.delete("/{content_id}", status_code=204)
def delete_content(content_id: int, db: Session = Depends(get_db)):
    repository = ContentRepositoryImpl(db)
    use_case = DeleteContentUseCase(repository)
    deleted = use_case.execute(content_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    return None