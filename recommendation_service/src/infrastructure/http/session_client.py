import httpx
from typing import Optional, Dict, Any
from src.infrastructure.config.settings import SESSION_SERVICE_URL, HTTP_TIMEOUT

class SessionClient:
    def __init__(self):
        self.base_url = SESSION_SERVICE_URL
        self.timeout = HTTP_TIMEOUT

    async def get_current_activity(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/sessions/{session_id}"
                )
                response.raise_for_status()
                data = response.json()
                
                if 'current_activity' in data:
                    return data['current_activity']
                return None
                
        except httpx.HTTPError as e:
            print(f"[ERROR] Error fetching session {session_id}: {str(e)}")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error fetching session: {str(e)}")
            return None