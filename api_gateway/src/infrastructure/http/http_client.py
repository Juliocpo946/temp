import httpx
from typing import Optional, Dict, Any

class HTTPClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)

    async def post(self, url: str, json: Dict[str, Any] = None, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            response = await self.client.post(url, json=json, headers=headers, params=params)
            response.raise_for_status()
            if response.text:
                return response.json()
            return {}
        except httpx.HTTPError as e:
            print(f"Error en petición POST a {url}: {str(e)}")
            raise

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            if response.text:
                return response.json()
            return {}
        except httpx.HTTPError as e:
            print(f"Error en petición GET a {url}: {str(e)}")
            raise

    async def put(self, url: str, json: Dict[str, Any] = None, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            response = await self.client.put(url, json=json, headers=headers, params=params)
            response.raise_for_status()
            if response.text:
                return response.json()
            return {}
        except httpx.HTTPError as e:
            print(f"Error en petición PUT a {url}: {str(e)}")
            raise

    async def patch(self, url: str, json: Dict[str, Any] = None, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            response = await self.client.patch(url, json=json, headers=headers, params=params)
            response.raise_for_status()
            if response.text:
                return response.json()
            return {}
        except httpx.HTTPError as e:
            print(f"Error en petición PATCH a {url}: {str(e)}")
            raise

    async def delete(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            response = await self.client.delete(url, headers=headers, params=params)
            response.raise_for_status()
            if response.text:
                return response.json()
            return {}
        except httpx.HTTPError as e:
            print(f"Error en petición DELETE a {url}: {str(e)}")
            raise

    async def close(self) -> None:
        await self.client.aclose()