import httpx
from typing import Optional, Dict, Any
from datetime import datetime
from src.infrastructure.config.settings import SESSION_SERVICE_URL, HTTP_TIMEOUT


class SessionClient:
    def __init__(self):
        self.base_url = SESSION_SERVICE_URL
        self.timeout = HTTP_TIMEOUT

    async def get_activity_details(self, activity_uuid: str) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/activities/{activity_uuid}/details"
                )

                if response.status_code == 200:
                    return response.json()
                return None

        except httpx.HTTPError:
            self._log_error(f"Error obteniendo detalles de actividad {activity_uuid}")
            return None
        except Exception:
            self._log_error(f"Error inesperado consultando actividad {activity_uuid}")
            return None

    def _log_error(self, message: str) -> None:
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [SESSION_CLIENT] [ERROR] {message}")