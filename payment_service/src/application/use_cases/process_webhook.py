from src.domain.repositories.payment_repository import PaymentRepository
from src.infrastructure.messaging.payment_event_publisher import PaymentEventPublisher
from src.infrastructure.payment_gateway.mercadopago_client import MercadoPagoClient


class ProcessWebhookUseCase:
    def __init__(
            self,
            payment_repo: PaymentRepository,
            event_publisher: PaymentEventPublisher,
            mp_client: MercadoPagoClient
    ):
        self.payment_repo = payment_repo
        self.event_publisher = event_publisher
        self.mp_client = mp_client

    def execute(self, notification_data: dict) -> dict:
        print(f"[WEBHOOK CASE] Procesando data: {notification_data}")

        # ... (logica de extraer ID y Topic) ...
        # (Asegúrate de tener esto igual que antes)
        topic = notification_data.get("type") or notification_data.get("topic")
        payment_id = notification_data.get("data", {}).get("id") or notification_data.get("id")

        if topic == "payment" and payment_id:
            print(f"[WEBHOOK CASE] Consultando pago {payment_id} a MP...")
            payment_info = self.mp_client.get_payment_info(payment_id)

            if not payment_info:
                print("[WEBHOOK CASE] ERROR: No se obtuvo info de MP")
                return {'status': 'error', 'message': 'Payment info not found in MP'}

            status = payment_info.get("status")
            print(f"[WEBHOOK CASE] Estado del pago en MP: {status}")

            if status == "approved":
                # ... (logica de external reference) ...
                external_reference = payment_info.get("external_reference")
                if not external_reference:
                    print("[WEBHOOK CASE] ERROR: Pago sin external_reference")
                    return {'status': 'ignored'}

                try:
                    app_id, comp_id = external_reference.split("|")
                except:
                    print(f"[WEBHOOK CASE] ERROR: Referencia malformada {external_reference}")
                    return {'status': 'ignored'}

                # PUBLICACIÓN
                print(f"[WEBHOOK CASE] Intentando publicar evento para App {app_id}...")
                success = self.event_publisher.publish_application_paid(
                    application_id=app_id,
                    company_id=comp_id,
                    amount=payment_info.get("transaction_amount", 0)
                )

                if success:
                    print("[WEBHOOK CASE] >>> ÉXITO: Evento publicado en RabbitMQ <<<")
                else:
                    print("[WEBHOOK CASE] >>> FATAL: Falló la publicación en RabbitMQ <<<")

                return {'status': 'processed', 'payment_id': payment_id}

        print(f"[WEBHOOK CASE] Ignorado. Topic: {topic}, Status: {status if 'status' in locals() else 'N/A'}")
        return {'status': 'ignored'}