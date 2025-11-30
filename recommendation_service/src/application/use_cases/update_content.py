from typing import Optional
from src.domain.entities.content import Content
from src.domain.repositories.content_repository import ContentRepository
from src.application.dtos.content_dto import UpdateContentDTO


class UpdateContentUseCase:
    def __init__(self, content_repository: ContentRepository):
        self.content_repository = content_repository

    def execute(self, content_id: int, dto: UpdateContentDTO) -> Optional[Content]:
        content = self.content_repository.get_by_id(content_id)
        if not content:
            return None

        content.update(
            tema=dto.tema,
            subtema=dto.subtema,
            tipo_actividad=dto.tipo_actividad,
            tipo_intervencion=dto.tipo_intervencion,
            contenido=dto.contenido,
            activo=dto.activo
        )

        return self.content_repository.update(content)