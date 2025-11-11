from datetime import datetime
from src.domain.entities.log import Log
from src.domain.repositories.log_repository import LogRepository
from src.domain.value_objects.log_level import LogLevel
from src.application.dtos.log_dto import LogDTO

class SaveLogUseCase:
    def __init__(self, log_repo: LogRepository):
        self.log_repo = log_repo

    def execute(self, service: str, level: str, message: str) -> dict:
        if not LogLevel.is_valid(level):
            raise ValueError(f"Nivel de log inválido: {level}")

        log = Log(
            id=None,
            service=service,
            level=level,
            message=message,
            timestamp=datetime.utcnow()
        )

        saved_log = self.log_repo.save(log)

        log_dto = LogDTO(
            saved_log.id,
            saved_log.service,
            saved_log.level,
            saved_log.message,
            saved_log.timestamp
        )

        return log_dto.to_dict()