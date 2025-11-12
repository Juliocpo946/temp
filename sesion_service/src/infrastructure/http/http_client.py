import httpx
from typing import Optional, Dict, Any

class HTTPClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise

    async def close(self) -> None:
        await self.client.aclose()