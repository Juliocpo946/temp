import httpx
from typing import Optional, Dict, Any

class HTTPClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return None

    async def close(self) -> None:
        await self.client.aclose()