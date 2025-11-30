from src.domain.entities.content import Content
from src.domain.repositories.content_repository import ContentRepository
from src.application.dtos.content_dto import CreateContentDTO


class CreateContentUseCase:
    def __init__(self, content_repository: ContentRepository):
        self.content_repository = content_repository

    def execute(self, dto: CreateContentDTO) -> Content:
        content = Content(
            id=None,
            topic=dto.topic,
            subtopic=dto.subtopic,
            activity_type=dto.activity_type,
            intervention_type=dto.intervention_type,
            content=dto.content,
            active=dto.active
        )
        return self.content_repository.save(content)