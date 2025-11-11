from typing import Optional
from src.domain.repositories.log_repository import LogRepository
from src.application.dtos.log_dto import LogDTO

class GetLogsUseCase:
    def __init__(self, log_repo: LogRepository):
        self.log_repo = log_repo

    def execute(self, service: Optional[str] = None, level: Optional[str] = None, limit: int = 100) -> dict:
        if service and level:
            logs = self.log_repo.get_by_service_and_level(service, level, limit)
        elif service:
            logs = self.log_repo.get_by_service(service, limit)
        elif level:
            logs = self.log_repo.get_by_level(level, limit)
        else:
            logs = self.log_repo.get_all(limit)

        log_dtos = [
            LogDTO(
                log.id,
                log.service,
                log.level,
                log.message,
                log.timestamp
            ).to_dict()
            for log in logs
        ]

        return {'logs': log_dtos, 'total': len(log_dtos)}