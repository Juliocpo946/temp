from datetime import datetime

class Request:
    def __init__(self, correlation_id: str, api_key: str, service: str, method: str, path: str, status: int, timestamp: datetime):
        self.correlation_id = correlation_id
        self.api_key = api_key
        self.service = service
        self.method = method
        self.path = path
        self.status = status
        self.timestamp = timestamp