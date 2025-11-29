import hashlib

class HashingService:
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """
        Genera un hash SHA-256 de la API Key.
        Esto es lo que guardaremos en la base de datos.
        """
        return hashlib.sha256(api_key.encode('utf-8')).hexdigest()