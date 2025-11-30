from typing import Optional
from src.domain.entities.content import Content
from src.domain.repositories.content_repository import ContentRepository


class GetContentUseCase:
    def __init__(self, content_repository: ContentRepository):
        self.content_repository = content_repository

    def execute(self, content_id: int) -> Optional[Content]:
        return self.content_repository.get_by_id(content_id)