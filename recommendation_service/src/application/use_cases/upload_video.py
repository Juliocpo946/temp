import uuid
from typing import Dict, Any
from src.domain.entities.content import Content
from src.domain.repositories.content_repository import ContentRepository
from src.infrastructure.http.cloudinary_client import CloudinaryClient
from src.application.dtos.content_dto import CreateContentFromUploadDTO


class UploadVideoUseCase:
    def __init__(
        self,
        content_repository: ContentRepository,
        cloudinary_client: CloudinaryClient
    ):
        self.content_repository = content_repository
        self.cloudinary_client = cloudinary_client

    def execute(
        self,
        file_content: bytes,
        filename: str,
        dto: CreateContentFromUploadDTO
    ) -> Dict[str, Any]:
        upload_result = self.cloudinary_client.upload_video(
            file_content=file_content,
            company_id=dto.company_id,
            filename=filename
        )

        if not upload_result.get("success"):
            return {
                "success": False,
                "error": upload_result.get("error", "Error desconocido al subir video")
            }

        content = Content(
            id=None,
            company_id=uuid.UUID(dto.company_id),
            topic=dto.topic,
            subtopic=dto.subtopic,
            activity_type=dto.activity_type,
            intervention_type=dto.intervention_type,
            content_url=upload_result.get("url"),
            content_type="video",
            active=dto.active
        )

        saved_content = self.content_repository.save(content)

        return {
            "success": True,
            "content": saved_content.to_dict(),
            "video_info": {
                "url": upload_result.get("url"),
                "public_id": upload_result.get("public_id"),
                "duration": upload_result.get("duration"),
                "format": upload_result.get("format")
            }
        }