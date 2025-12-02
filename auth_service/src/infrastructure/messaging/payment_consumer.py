import json
import time
import threading
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import PAYMENT_EVENTS_QUEUE
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.repositories.application_repository_impl import ApplicationRepositoryImpl
from src.infrastructure.persistence.repositories.company_repository_impl import CompanyRepositoryImpl
from src.infrastructure.persistence.repositories.api_key_repository_impl import ApiKeyRepositoryImpl
from src.application.use_cases.generate_new_api_key import GenerateNewApiKeyUseCase


class PaymentConsumer:
    def __init__(self):
        self.rabbitmq_client = RabbitMQClient()
        self.queue_name = PAYMENT_EVENTS_QUEUE
        self._running = False

    def start(self) -> None:
        self._running = True
        thread = threading.Thread(target=self._consume_loop, daemon=True)
        thread.start()
        print(f"[PAYMENT_CONSUMER] Iniciado en cola: {self.queue_name}")

    def _consume_loop(self) -> None:
        while self._running:
            try:
                self.rabbitmq_client.declare_queue(self.queue_name)
                self.rabbitmq_client.consume(self.queue_name, self._callback)
            except Exception as e:
                print(f"[PAYMENT_CONSUMER] Error de conexión: {e}. Reintentando en 5s...")
                time.sleep(5)
                # Forzar reconexión del cliente interno si es necesario
                try:
                    self.rabbitmq_client.connect()
                except:
                    pass

    def _callback(self, ch, method, properties, body) -> None:
        print(f"[PAYMENT_CONSUMER] Mensaje recibido: {body}")  # DEBUG

        db = SessionLocal()
        try:
            message = json.loads(body)
            event_type = message.get("type")

            if event_type == "application_paid":
                self._handle_application_paid(db, message)
            else:
                print(f"[PAYMENT_CONSUMER] Ignorando evento desconocido: {event_type}")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"[PAYMENT_CONSUMER] Error procesando mensaje: {str(e)}")
            # Nack sin requeue si es error de datos, con requeue si es de sistema
            # Por seguridad, hacemos nack(requeue=False) para no ciclar infinitamente en errores de lógica
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        finally:
            db.close()

    def _handle_application_paid(self, db, message: dict) -> None:
        application_id = message.get("application_id")

        print(f"[PAYMENT_CONSUMER] Procesando activación para app: {application_id}")

        app_repo = ApplicationRepositoryImpl(db)
        company_repo = CompanyRepositoryImpl(db)
        api_key_repo = ApiKeyRepositoryImpl(db)

        # 1. Obtener la aplicación
        application = app_repo.get_by_id(application_id)
        if not application:
            print(f"[PAYMENT_CONSUMER] ERROR: Aplicacion {application_id} no encontrada en BD")
            return

        # 2. Idempotencia
        if application.is_active:
            print(f"[PAYMENT_CONSUMER] WARN: Aplicacion {application_id} ya estaba activa")
            return

        # 3. Activar
        application.activate()
        app_repo.update(application)
        print(f"[PAYMENT_CONSUMER] SUCCESS: Aplicacion activada")

        # 4. Generar Key
        try:
            use_case = GenerateNewApiKeyUseCase(
                app_repo,
                company_repo,
                api_key_repo,
                self.rabbitmq_client
            )
            result = use_case.execute(str(application.id))
            print(f"[PAYMENT_CONSUMER] SUCCESS: API Key generada y enviada")
        except Exception as e:
            print(f"[PAYMENT_CONSUMER] ERROR generando API Key: {e}")