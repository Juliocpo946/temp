import stripe
from src.infrastructure.config.settings import STRIPE_API_KEY, APP_CREATION_PRICE_MXN

stripe.api_key = STRIPE_API_KEY

class StripeClient:
    def create_checkout_session(self, application_id: str, company_id: str, customer_email: str, success_url: str, cancel_url: str) -> dict:
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'mxn',
                        'product_data': {
                            'name': 'Activación de Aplicación',
                            'description': f'Pago único para activar aplicación {application_id}'
                        },
                        'unit_amount': APP_CREATION_PRICE_MXN * 100, # En centavos
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
                metadata={
                    'type': 'app_activation',
                    'application_id': application_id,
                    'company_id': company_id
                }
            )
            return {'url': session.url, 'id': session.id}
        except Exception as e:
            print(f"[STRIPE] Error creando sesión: {str(e)}")
            raise

    def construct_event(self, payload: bytes, sig_header: str, secret: str):
        return stripe.Webhook.construct_event(payload, sig_header, secret)