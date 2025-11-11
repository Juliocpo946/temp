from typing import Optional, List
from src.domain.entities.log import Log
from src.domain.repositories.log_repository import LogRepository
from src.infrastructure.persistence.models.log_model import LogModel

class LogRepositoryImpl(LogRepository):
    def save(self, log: Log) -> Log:
        db_log = LogModel(
            service=log.service,
            level=log.level,
            message=log.message,
            timestamp=log.timestamp
        )
        db_log.save()
        return self._to_domain(db_log)

    def get_by_id(self, log_id: str) -> Optional[Log]:
        db_log = LogModel.objects(id=log_id).first()
        return self._to_domain(db_log) if db_log else None

    def get_by_service(self, service: str, limit: int = 100) -> List[Log]:
        db_logs = LogModel.objects(service=service).order_by('-timestamp').limit(limit)
        return [self._to_domain(log) for log in db_logs]

    def get_by_level(self, level: str, limit: int = 100) -> List[Log]:
        db_logs = LogModel.objects(level=level).order_by('-timestamp').limit(limit)
        return [self._to_domain(log) for log in db_logs]

    def get_all(self, limit: int = 100) -> List[Log]:
        db_logs = LogModel.objects().order_by('-timestamp').limit(limit)
        return [self._to_domain(log) for log in db_logs]

    def get_by_service_and_level(self, service: str, level: str, limit: int = 100) -> List[Log]:
        db_logs = LogModel.objects(service=service, level=level).order_by('-timestamp').limit(limit)
        return [self._to_domain(log) for log in db_logs]

    @staticmethod
    def _to_domain(db_log: LogModel) -> Log:
        return Log(
            id=str(db_log.id),
            service=db_log.service,
            level=db_log.level,
            message=db_log.message,
            timestamp=db_log.timestamp
        )