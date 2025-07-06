import pika
import os
import json
from app.config import RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS, RABBITMQ_QUEUE


def get_rabbitmq_connection():
    """
    Establece una conexión con RabbitMQ utilizando las credenciales del entorno.
    Retorna el objeto de conexión si tiene éxito, None en caso contrario.
    """
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=600 # Aumentar heartbeat para conexiones de larga duración
        )
        connection = pika.BlockingConnection(parameters)
        return connection
    except pika.exceptions.AMQPConnectionError as e:
        print(f"ERROR: No se pudo conectar a RabbitMQ en {RABBITMQ_HOST}:{RABBITMQ_PORT}. Error: {e}", file=os.sys.stderr)
        return None
    except Exception as e:
        print(f"ERROR inesperado al intentar conectar a RabbitMQ: {e}", file=os.sys.stderr)
        return None

def publish_message(message: dict):
    """
    Publica un mensaje en la cola de RabbitMQ.
    El mensaje se serializa a JSON y se marca como persistente.
    """
    connection = None
    try:
        connection = get_rabbitmq_connection()
        if connection:
            channel = connection.channel()
            # Declara la cola. durable=True asegura que la cola persiste si RabbitMQ se reinicia.
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            
            # Publica el mensaje. delivery_mode=2 marca el mensaje como persistente.
            channel.basic_publish(
                exchange='', # Usamos el exchange por defecto
                routing_key=RABBITMQ_QUEUE,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                )
            )
            print(f"Mensaje publicado en RabbitMQ para user_id: {message.get('user_id', 'N/A')}")
    except Exception as e:
        print(f"ERROR al publicar mensaje en RabbitMQ: {e}", file=os.sys.stderr)
    finally:
        if connection:
            connection.close()

def consume_messages():
    """
    Consume todos los mensajes disponibles actualmente en la cola de RabbitMQ.
    Retorna una lista de diccionarios (mensajes JSON parseados).
    """
    messages = []
    connection = None
    try:
        connection = get_rabbitmq_connection()
        if connection:
            channel = connection.channel()
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

            # Usar basic_get para obtener todos los mensajes de una vez.
            # auto_ack=True: los mensajes se eliminan de la cola automáticamente después de ser leídos.
            while True:
                method_frame, properties, body = channel.basic_get(queue=RABBITMQ_QUEUE, auto_ack=True)
                if method_frame:
                    messages.append(json.loads(body.decode('utf-8')))
                else:
                    # No hay más mensajes en la cola
                    break
            return messages
    except Exception as e:
        print(f"ERROR al consumir mensajes de RabbitMQ: {e}", file=os.sys.stderr)
        return []
    finally:
        if connection:
            connection.close()
