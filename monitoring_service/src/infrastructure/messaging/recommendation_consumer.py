import json
import threading
import asyncio
import pika
from concurrent.futures import ThreadPoolExecutor
from src.infrastructure.config.settings import (
    RECOMMENDATIONS_QUEUE,
    AMQP_URL,
    RECOMMENDATION_CONSUMER_WORKERS,
    RECOMMENDATION_PREFETCH_COUNT
)
from src.infrastructure.websocket.connection_manager import manager


class RecommendationConsumer:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=RECOMMENDATION_CONSUMER_WORKERS)
        self._running = False
        self._connection = None
        self._channel = None
        self._loop = None

    def set_event_loop(self, loop):
        self._loop = loop

    def start(self) -> None:
        self._running = True
        thread = threading.Thread(target=self._consume, daemon=True)
        thread.start()
        print(f"[RECOMMENDATION_CONSUMER] [INFO] Consumer iniciado con {RECOMMENDATION_CONSUMER_WORKERS} workers")

    def _consume(self) -> None:
        while self._running:
            try:
                parameters = pika.URLParameters(AMQP_URL)
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()
                
                # CORRECCIÓN: Eliminados los argumentos de DLQ para evitar conflicto con la cola existente
                self._channel.queue_declare(
                    queue=RECOMMENDATIONS_QUEUE, 
                    durable=True
                )
                
                self._channel.basic_qos(prefetch_count=RECOMMENDATION_PREFETCH_COUNT)
                
                self._channel.basic_consume(
                    queue=RECOMMENDATIONS_QUEUE,
                    on_message_callback=self._on_message,
                    auto_ack=False
                )
                
                print(f"[RECOMMENDATION_CONSUMER] [INFO] Escuchando en cola: {RECOMMENDATIONS_QUEUE}")
                self._channel.start_consuming()
            except Exception as e:
                print(f"[RECOMMENDATION_CONSUMER] [ERROR] Error en consumer: {str(e)}")
                if self._running:
                    import time
                    time.sleep(5)

    def _on_message(self, ch, method, properties, body) -> None:
        self.executor.submit(self._process_message, ch, method, properties, body)

    def _process_message(self, ch, method, properties, body) -> None:
        try:
            message = json.loads(body)
            
            # Intentar obtener el ID de conexión WS
            activity_uuid = message.get("contexto", {}).get("activity_uuid")
            
            if not activity_uuid:
                 # Fallback: a veces viene en metadata
                 activity_uuid = message.get("metadata", {}).get("activity_uuid")

            if activity_uuid:
                # Intentar enviar al WebSocket local
                if self._loop and manager.has_connection(activity_uuid):
                    future = asyncio.run_coroutine_threadsafe(
                        manager.send_personal_message(message, activity_uuid),
                        self._loop
                    )
                    try:
                        future.result(timeout=2)
                        print(f"[RECOMMENDATION_CONSUMER] [INFO] Enviado a WS local: {activity_uuid}")
                    except Exception as e:
                        print(f"[RECOMMENDATION_CONSUMER] [ERROR] Fallo envio WS: {e}")
                else:
                     # Si no está conectado localmente, logueamos y continuamos
                     # En un entorno real distribuido, aquí podríamos intentar reenviar a otro nodo,
                     # pero para este caso asumimos que si no está aquí, no está conectado.
                     pass 
            
            # Siempre hacer ACK para evitar bucles infinitos
            self._safe_ack(ch, method.delivery_tag)

        except Exception as e:
            print(f"[RECOMMENDATION_CONSUMER] [ERROR] Error procesando mensaje: {str(e)}")
            # En caso de error, descartar (NACK sin requeue) para evitar bucles
            self._safe_nack(ch, method.delivery_tag, requeue=False)

    def _safe_ack(self, ch, delivery_tag) -> None:
        try:
            self._connection.add_callback_threadsafe(
                lambda: ch.basic_ack(delivery_tag=delivery_tag)
            )
        except Exception as e:
            print(f"[RECOMMENDATION_CONSUMER] [ERROR] Error en ACK: {str(e)}")

    def _safe_nack(self, ch, delivery_tag, requeue=True) -> None:
        try:
            self._connection.add_callback_threadsafe(
                lambda: ch.basic_nack(delivery_tag=delivery_tag, requeue=requeue)
            )
        except Exception as e:
            print(f"[RECOMMENDATION_CONSUMER] [ERROR] Error en NACK: {str(e)}")

    def close(self) -> None:
        self._running = False
        try:
            if self._connection and not self._connection.is_closed:
                self._connection.close()
        except Exception as e:
             print(f"[RECOMMENDATION_CONSUMER] [ERROR] Error cerrando consumer: {str(e)}")
        self.executor.shutdown(wait=False)
        print(f"[RECOMMENDATION_CONSUMER] [INFO] Consumer de recomendaciones cerrado")