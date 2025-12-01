import cloudinary
import cloudinary.uploader
from typing import Optional, Dict, Any
from src.infrastructure.config.settings import (
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET
)


class CloudinaryClient:
    def __init__(self):
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET
        )

    def upload_video(
        self,
        file_content: bytes,
        company_id: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            folder = f"sentiment-analyzer/{company_id}/videos"

            upload_options = {
                "resource_type": "video",
                "folder": folder,
                "overwrite": True,
                "invalidate": True
            }

            if filename:
                name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
                upload_options["public_id"] = name_without_ext

            result = cloudinary.uploader.upload(
                file_content,
                **upload_options
            )

            print(f"[CLOUDINARY_CLIENT] [INFO] Video subido exitosamente: {result.get('secure_url')}")

            return {
                "success": True,
                "url": result.get("secure_url"),
                "public_id": result.get("public_id"),
                "format": result.get("format"),
                "duration": result.get("duration"),
                "width": result.get("width"),
                "height": result.get("height"),
                "bytes": result.get("bytes")
            }

        except Exception as e:
            print(f"[CLOUDINARY_CLIENT] [ERROR] Error subiendo video: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def delete_video(self, public_id: str) -> bool:
        try:
            result = cloudinary.uploader.destroy(
                public_id,
                resource_type="video"
            )
            return result.get("result") == "ok"
        except Exception as e:
            print(f"[CLOUDINARY_CLIENT] [ERROR] Error eliminando video: {str(e)}")
            return False

    def get_video_info(self, public_id: str) -> Optional[Dict[str, Any]]:
        try:
            result = cloudinary.api.resource(
                public_id,
                resource_type="video"
            )
            return {
                "url": result.get("secure_url"),
                "format": result.get("format"),
                "duration": result.get("duration"),
                "width": result.get("width"),
                "height": result.get("height")
            }
        except Exception as e:
            print(f"[CLOUDINARY_CLIENT] [ERROR] Error obteniendo info de video: {str(e)}")
            return None