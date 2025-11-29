import pika
import json
import os

AMQP_URL = "amqps://siptuvyg:BZ2HUpBpSm_NNkGuRJYMviNrvLGYu7lm@gorilla.lmq.cloudamqp.com/siptuvyg"


def callback(ch, method, properties, body):
    print("\n[!] Evento Recibido:")
    data = json.loads(body)
    print(json.dumps(data, indent=2))


def start_listening():
    try:
        params = pika.URLParameters(AMQP_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()


        channel.queue_declare(queue='session_events', durable=True)

        print(' [*] Esperando eventos en la cola "session_events". Para salir presiona CTRL+C')

        channel.basic_consume(
            queue='session_events',
            on_message_callback=callback,
            auto_ack=True
        )

        channel.start_consuming()
    except KeyboardInterrupt:
        print('Interrumpido')
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    start_listening()