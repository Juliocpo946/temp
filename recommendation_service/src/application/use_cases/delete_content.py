from src.domain.repositories.content_repository import ContentRepository


class DeleteContentUseCase:
    def __init__(self, content_repository: ContentRepository):
        self.content_repository = content_repository

    def execute(self, content_id: int) -> bool:
        return self.content_repository.delete(content_id)