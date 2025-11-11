from datetime import datetime

class RequestDTO:
    def __init__(self, correlation_id: str, api_key: str, service: str, method: str, path: str, status: int, timestamp: datetime):
        self.correlation_id = correlation_id
        self.api_key = api_key
        self.service = service
        self.method = method
        self.path = path
        self.status = status
        self.timestamp = timestamp

    def to_dict(self) -> dict:
        return {
            'correlation_id': self.correlation_id,
            'api_key': self.api_key[:10] if self.api_key else None,
            'service': self.service,
            'method': self.method,
            'path': self.path,
            'status': self.status,
            'timestamp': self.timestamp.isoformat()
        }