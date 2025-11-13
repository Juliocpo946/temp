import httpx
from typing import Optional, Dict, Any
from src.infrastructure.config.settings import CONTENT_SERVICE_URL, HTTP_TIMEOUT

class ContentClient:
    def __init__(self):
        self.base_url = CONTENT_SERVICE_URL
        self.timeout = HTTP_TIMEOUT

    async def search_specific(
        self,
        recommendation_type: str,
        title: str,
        subtitle: str,
        activity_type: str,
        precision_min: float,
        precision_max: float,
        evento: str
    ) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    'title': title,
                    'subtitle': subtitle,
                    'activity_type': activity_type,
                    'precision_min': precision_min,
                    'precision_max': precision_max,
                    'evento': evento,
                    'nivel': 'especifico'
                }
                
                response = await client.get(
                    f"{self.base_url}/content/type/{recommendation_type}",
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
                
        except httpx.HTTPError as e:
            print(f"[ERROR] Error searching specific content: {str(e)}")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error in specific search: {str(e)}")
            return None

    async def search_generic(
        self,
        recommendation_type: str,
        activity_type: str,
        precision_min: float,
        precision_max: float,
        evento: str
    ) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    'activity_type': activity_type,
                    'precision_min': precision_min,
                    'precision_max': precision_max,
                    'evento': evento,
                    'nivel': 'generico'
                }
                
                response = await client.get(
                    f"{self.base_url}/content/type/{recommendation_type}",
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
                
        except httpx.HTTPError as e:
            print(f"[ERROR] Error searching generic content: {str(e)}")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error in generic search: {str(e)}")
            return None