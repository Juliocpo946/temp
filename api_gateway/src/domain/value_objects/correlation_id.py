import uuid

class CorrelationId:
    def __init__(self, value: str = None):
        self.value = value or str(uuid.uuid4())

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other) -> bool:
        if isinstance(other, CorrelationId):
            return self.value == other.value
        return self.value == other