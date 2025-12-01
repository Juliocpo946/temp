from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Header
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories.content_repository_impl import ContentRepositoryImpl
from src.infrastructure.http.cloudinary_client import CloudinaryClient
from src.application.dtos.content_dto import CreateContentDTO, UpdateContentDTO, ContentFilterDTO, CreateContentFromUploadDTO
from src.application.use_cases.create_content import CreateContentUseCase
from src.application.use_cases.update_content import UpdateContentUseCase
from src.application.use_cases.delete_content import DeleteContentUseCase
from src.application.use_cases.get_content import GetContentUseCase
from src.application.use_cases.list_contents import ListContentsUseCase
from src.application.use_cases.upload_video import UploadVideoUseCase

router = APIRouter()


@router.post("/upload", status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    topic: str = Form(...),
    intervention_type: str = Form(...),
    subtopic: Optional[str] = Form(None),
    activity_type: Optional[str] = Form(None),
    active: bool = Form(True),
    x_company_id: str = Header(..., alias="X-Company-ID"),
    db: Session = Depends(get_db)
):
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un video")

    max_size = 100 * 1024 * 1024
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(status_code=400, detail="El archivo excede el tamano maximo de 100MB")

    repository = ContentRepositoryImpl(db)
    cloudinary_client = CloudinaryClient()
    use_case = UploadVideoUseCase(repository, cloudinary_client)

    dto = CreateContentFromUploadDTO(
        company_id=x_company_id,
        topic=topic,
        subtopic=subtopic,
        activity_type=activity_type,
        intervention_type=intervention_type,
        active=active
    )

    result = use_case.execute(
        file_content=file_content,
        filename=file.filename,
        dto=dto
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))

    return result


@router.post("/", status_code=201)
def create_content(
    dto: CreateContentDTO,
    x_company_id: str = Header(..., alias="X-Company-ID"),
    db: Session = Depends(get_db)
):
    if dto.company_id != x_company_id:
        raise HTTPException(status_code=403, detail="No autorizado para crear contenido para otra empresa")

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
    x_company_id: str = Header(..., alias="X-Company-ID"),
    db: Session = Depends(get_db)
):
    repository = ContentRepositoryImpl(db)
    use_case = ListContentsUseCase(repository)
    filters = ContentFilterDTO(
        company_id=x_company_id,
        topic=topic,
        subtopic=subtopic,
        activity_type=activity_type,
        intervention_type=intervention_type,
        active=active
    )
    contents = use_case.execute(filters)
    return [c.to_dict() for c in contents]


@router.get("/{content_id}")
def get_content(
    content_id: int,
    x_company_id: str = Header(..., alias="X-Company-ID"),
    db: Session = Depends(get_db)
):
    repository = ContentRepositoryImpl(db)
    use_case = GetContentUseCase(repository)
    content = use_case.execute(content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    if str(content.company_id) != x_company_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    return content.to_dict()


@router.put("/{content_id}")
def update_content(
    content_id: int,
    dto: UpdateContentDTO,
    x_company_id: str = Header(..., alias="X-Company-ID"),
    db: Session = Depends(get_db)
):
    repository = ContentRepositoryImpl(db)

    existing = repository.get_by_id(content_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    if str(existing.company_id) != x_company_id:
        raise HTTPException(status_code=403, detail="No autorizado")

    use_case = UpdateContentUseCase(repository)
    content = use_case.execute(content_id, dto)
    return content.to_dict()


@router.delete("/{content_id}", status_code=204)
def delete_content(
    content_id: int,
    x_company_id: str = Header(..., alias="X-Company-ID"),
    db: Session = Depends(get_db)
):
    repository = ContentRepositoryImpl(db)

    existing = repository.get_by_id(content_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    if str(existing.company_id) != x_company_id:
        raise HTTPException(status_code=403, detail="No autorizado")

    use_case = DeleteContentUseCase(repository)
    deleted = use_case.execute(content_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    return None