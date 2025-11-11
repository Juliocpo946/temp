import httpx
from typing import Optional, Dict, Any

class HTTPClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def post(self, url: str, json: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        try:
            response = await self.client.post(url, json=json, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error en petición POST a {url}: {str(e)}")
            raise

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error en petición GET a {url}: {str(e)}")
            raise

    async def close(self) -> None:
        await self.client.aclose()