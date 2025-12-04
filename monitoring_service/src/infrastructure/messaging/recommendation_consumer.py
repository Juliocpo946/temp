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
        print(f"[RECOMMENDATION_CONSUMER] [INFO] Event loop configurado: {loop}")

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
            
            activity_uuid = message.get("contexto", {}).get("activity_uuid")
            
            if not activity_uuid:
                activity_uuid = message.get("metadata", {}).get("activity_uuid")

            if not activity_uuid:
                print(f"[RECOMMENDATION_CONSUMER] [WARNING] Mensaje sin activity_uuid, ignorando")
                self._safe_ack(ch, method.delivery_tag)
                return

            has_conn = manager.has_connection(activity_uuid)

            if self._loop and has_conn:
                message["type"] = "recommendation"
                
                future = asyncio.run_coroutine_threadsafe(
                    manager.send_personal_message(message, activity_uuid),
                    self._loop
                )
                try:
                    result = future.result(timeout=2)
                    print(f"[RECOMMENDATION_CONSUMER] [INFO] Enviado a WS local: {activity_uuid}, resultado: {result}")
                except Exception as e:
                    print(f"[RECOMMENDATION_CONSUMER] [ERROR] Fallo envio WS: {e}")
            else:
                if not self._loop:
                    print(f"[RECOMMENDATION_CONSUMER] [WARNING] No hay event loop configurado")
                if not has_conn:
                    print(f"[RECOMMENDATION_CONSUMER] [WARNING] No hay conexion activa para: {activity_uuid}")
            
            self._safe_ack(ch, method.delivery_tag)

        except Exception as e:
            print(f"[RECOMMENDATION_CONSUMER] [ERROR] Error procesando mensaje: {str(e)}")
            import traceback
            traceback.print_exc()
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