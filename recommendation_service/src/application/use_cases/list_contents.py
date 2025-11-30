from typing import List
from src.domain.entities.content import Content
from src.domain.repositories.content_repository import ContentRepository
from src.application.dtos.content_dto import ContentFilterDTO


class ListContentsUseCase:
    def __init__(self, content_repository: ContentRepository):
        self.content_repository = content_repository

    def execute(self, filters: ContentFilterDTO) -> List[Content]:
        return self.content_repository.list_all(
            tema=filters.tema,
            subtema=filters.subtema,
            tipo_actividad=filters.tipo_actividad,
            tipo_intervencion=filters.tipo_intervencion,
            activo=filters.activo
        )