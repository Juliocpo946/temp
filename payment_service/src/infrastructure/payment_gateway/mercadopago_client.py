import mercadopago
import json
from src.infrastructure.config.settings import MERCADOPAGO_ACCESS_TOKEN, APP_CREATION_PRICE_MXN, MP_WEBHOOK_URL


class MercadoPagoClient:
    def __init__(self):
        self.sdk = mercadopago.SDK(MERCADOPAGO_ACCESS_TOKEN)

    def create_preference(self, application_id: str, company_id: str, email: str, success_url: str,
                          failure_url: str) -> dict:
        try:
            preference_data = {
                "items": [
                    {
                        "id": "app_activation",
                        "title": "Activación de Aplicación - API Key",
                        "quantity": 1,
                        "currency_id": "MXN",
                        "unit_price": float(APP_CREATION_PRICE_MXN)
                    }
                ],
                "payer": {
                    "email": email
                },
                "back_urls": {
                    "success": success_url,
                    "failure": failure_url,
                    "pending": failure_url
                },
                "auto_return": "approved",
                "external_reference": f"{application_id}|{company_id}",
                "notification_url": MP_WEBHOOK_URL
            }

            print(f"[MP DEBUG] Enviando preferencia a MP: {json.dumps(preference_data)}")

            # Llamada al SDK
            preference_response = self.sdk.preference().create(preference_data)

            # --- DEBUG CRÍTICO ---
            print(f"[MP DEBUG] Respuesta completa de MP: {preference_response}")

            # Validar status HTTP de MP (201 es creado)
            if preference_response["status"] not in [200, 201]:
                error_msg = preference_response.get("response", {}).get("message", "Error desconocido de MP")
                print(f"[MP ERROR] MercadoPago rechazó la creación: {error_msg}")
                raise ValueError(f"MercadoPago Error: {error_msg}")

            preference = preference_response["response"]

            init_point = preference.get("init_point")
            pref_id = preference.get("id")

            if not init_point:
                print("[MP ERROR] La respuesta no tiene 'init_point'")
                raise ValueError("MercadoPago no devolvió URL de pago")

            return {
                "url": init_point,
                "id": pref_id
            }

        except Exception as e:
            print(f"[MERCADOPAGO EXCEPTION] {str(e)}")
            raise e  # Re-lanzar para que el controller devuelva 500

    def get_payment_info(self, payment_id: str) -> dict:
        try:
            payment_response = self.sdk.payment().get(payment_id)
            return payment_response["response"]
        except Exception as e:
            print(f"[MERCADOPAGO] Error obteniendo info del pago {payment_id}: {str(e)}")
            return None