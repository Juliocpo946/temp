from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.repositories.session_repository_impl import SessionRepositoryImpl
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient


class SessionExpirationJob:
    def __init__(self):
        self.rabbitmq_client = RabbitMQClient()

    def mark_paused_sessions(self):
        """Busca sesiones activas sin heartbeat reciente y las pausa automáticamente"""
        db = SessionLocal()
        try:
            repo = SessionRepositoryImpl(db)
            # 30 segundos sin heartbeat = pausa automática
            sessions = repo.get_sessions_without_heartbeat(30)

            for session in sessions:
                session.mark_paused_automatically()
                repo.update(session)
                self._publish_log(f"Sesión {session.id} pausada automáticamente por inactividad", "info")
        except Exception as e:
            print(f"Error en job mark_paused_sessions: {str(e)}")
        finally:
            db.close()

    def mark_expired_sessions(self):
        """Busca sesiones pausadas por mucho tiempo y las marca como expiradas"""
        db = SessionLocal()
        try:
            repo = SessionRepositoryImpl(db)
            # 1 hora en pausa = expirada
            sessions = repo.get_inactive_sessions(1)

            for session in sessions:
                session.mark_expired()
                repo.update(session)
                self._publish_log(f"Sesión {session.id} expirada por tiempo límite", "warning")
        except Exception as e:
            print(f"Error en job mark_expired_sessions: {str(e)}")
        finally:
            db.close()

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'session-service',
            'level': level,
            'message': message
        }
        try:
            self.rabbitmq_client.publish('logs', log_message)
        except Exception as e:
            print(f"Error publicando log desde job: {str(e)}")