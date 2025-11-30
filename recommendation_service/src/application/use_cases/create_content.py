from src.domain.entities.content import Content
from src.domain.repositories.content_repository import ContentRepository
from src.application.dtos.content_dto import CreateContentDTO


class CreateContentUseCase:
    def __init__(self, content_repository: ContentRepository):
        self.content_repository = content_repository

    def execute(self, dto: CreateContentDTO) -> Content:
        content = Content(
            id=None,
            tema=dto.tema,
            subtema=dto.subtema,
            tipo_actividad=dto.tipo_actividad,
            tipo_intervencion=dto.tipo_intervencion,
            contenido=dto.contenido,
            activo=dto.activo
        )
        return self.content_repository.save(content)