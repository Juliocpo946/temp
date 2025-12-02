from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories.payment_repository_impl import PaymentRepositoryImpl
from src.infrastructure.payment_gateway.mercadopago_client import MercadoPagoClient
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.messaging.payment_event_publisher import PaymentEventPublisher
from src.application.use_cases.create_payment_intent import CreatePaymentIntentUseCase
from src.application.use_cases.process_webhook import ProcessWebhookUseCase
from src.presentation.schemas.payment_schema import CreatePaymentLinkSchema

router = APIRouter(prefix="/payments", tags=["payments"])

# Instancias
mp_client = MercadoPagoClient()
rabbitmq_client = RabbitMQClient()
event_publisher = PaymentEventPublisher(rabbitmq_client)



@router.post("/create-link")
def create_payment_link(
        data: CreatePaymentLinkSchema,
        request: Request,
        db: Session = Depends(get_db)
):
    # ... (código de headers igual que tenías) ...
    company_id = request.headers.get("X-Company-ID")
    email = request.headers.get("X-User-Email")

    if not company_id or not email:
        # ...
        pass

    try:
        payment_repo = PaymentRepositoryImpl(db)
        use_case = CreatePaymentIntentUseCase(payment_repo, mp_client)

        print(f"[ROUTE DEBUG] Ejecutando use case para {email}...")

        result = use_case.execute(
            application_id=data.application_id,
            company_id=company_id,
            email=email,
            success_url=str(data.success_url),
            cancel_url=str(data.cancel_url)
        )

        print(f"[ROUTE DEBUG] Resultado del Use Case: {result}")  # <--- ESTO ES VITAL

        return result

    except ValueError as e:
        print(f"[ROUTE ERROR] ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[ROUTE ERROR] Exception: {e}")
        raise HTTPException(status_code=500, detail="Error interno procesando pago")

@router.post("/webhook")
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
    # MercadoPago envía los datos en query params (topic, id) O en el body.
    # Generalmente en el body para Webhooks v2.

    query_params = request.query_params
    try:
        body = await request.json()
    except:
        body = {}

    # Combinamos para buscar los datos
    notification_data = {**query_params, **body}

    print(f"[WEBHOOK] Datos recibidos: {notification_data}")

    try:
        payment_repo = PaymentRepositoryImpl(db)
        # Pasamos el cliente MP al caso de uso para que pueda consultar el estado
        use_case = ProcessWebhookUseCase(payment_repo, event_publisher, mp_client)
        result = use_case.execute(notification_data)
        return result
    except Exception as e:
        print(f"Error en webhook: {e}")
        # Siempre responder 200 a MP para que no reintente infinitamente si es un error lógico
        return {"status": "error", "message": str(e)}