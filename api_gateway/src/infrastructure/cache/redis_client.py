import redis
import json
from typing import Optional, Dict, Any
from src.infrastructure.config.settings import REDIS_URL

class RedisClient:
    def __init__(self):
        self.client = redis.from_url(REDIS_URL, decode_responses=True)

    def get_api_key(self, key_value: str) -> Optional[Dict[str, Any]]:
        try:
            data = self.client.get(f"apikey:{key_value}")
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Error al obtener de Redis: {str(e)}")
            return None

    def set_api_key(self, key_value: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        try:
            self.client.setex(f"apikey:{key_value}", ttl, json.dumps(data))
            return True
        except Exception as e:
            print(f"Error al guardar en Redis: {str(e)}")
            return False

    def delete_api_key(self, key_value: str) -> bool:
        try:
            self.client.delete(f"apikey:{key_value}")
            return True
        except Exception as e:
            print(f"Error al eliminar de Redis: {str(e)}")
            return False

    def increment_usage(self, application_id: str, date: str) -> int:
        try:
            key = f"usage:{application_id}:{date}"
            count = self.client.incr(key)
            if count == 1:
                self.client.expire(key, 604800)
            return count
        except Exception as e:
            print(f"Error al incrementar uso: {str(e)}")
            return 0

    def increment_bandwidth(self, application_id: str, date: str, bytes_count: int) -> int:
        try:
            key = f"bandwidth:{application_id}:{date}"
            total = self.client.incrby(key, bytes_count)
            if total == bytes_count:
                self.client.expire(key, 604800)
            return total
        except Exception as e:
            print(f"Error al incrementar bandwidth: {str(e)}")
            return 0

    def get_usage(self, application_id: str, date: str) -> int:
        try:
            value = self.client.get(f"usage:{application_id}:{date}")
            return int(value) if value else 0
        except Exception as e:
            print(f"Error al obtener uso: {str(e)}")
            return 0

    def close(self):
        self.client.close()