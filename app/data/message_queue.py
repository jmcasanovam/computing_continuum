import pika
import os
import json
import sys
import time
from datetime import datetime
from app.config import RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS

# Definir los nombres de las dos colas
EDGE_INGEST_QUEUE = "edge_ingest_queue"           # Cola donde el Edge publica y el Ingestor consume
INGEST_FOG_NOTIFICATION_QUEUE = "ingest_fog_notification_queue" # Cola donde el Ingestor publica y el Fog consume


def get_rabbitmq_connection(retries=15, initial_delay=5, max_delay=60):
    """
    Establece una conexión con RabbitMQ utilizando las credenciales del entorno, con reintentos.
    Retorna el objeto de conexión si tiene éxito, None en caso contrario.
    """
    conn = None
    delay = initial_delay
    for i in range(retries):
        try:
            # print(f"Intentando conectar a RabbitMQ ({i+1}/{retries}) en {RABBITMQ_HOST}:{RABBITMQ_PORT}...", file=sys.stderr)
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600
            )
            conn = pika.BlockingConnection(parameters)
            # print("Conexión a RabbitMQ exitosa.", file=sys.stderr)
            return conn
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Error operacional al conectar a RabbitMQ: {e}. Reintentando en {delay} segundos...", file=sys.stderr)
            time.sleep(delay)
            delay = min(delay * 1.5, max_delay)
        except Exception as e:
            print(f"Error inesperado al intentar conectar a RabbitMQ: {e}", file=sys.stderr)
            return None
    print(f"Falló la conexión a RabbitMQ después de {retries} intentos.", file=sys.stderr)
    return None

def publish_data_message(message: dict):
    """
    Publica un mensaje de datos en la cola de ingesta (EDGE_INGEST_QUEUE).
    """
    connection = None
    try:
        connection = get_rabbitmq_connection()
        if connection:
            channel = connection.channel()
            # Declarar la cola de ingesta
            channel.queue_declare(queue=EDGE_INGEST_QUEUE, durable=True)
            
            # Publicar el mensaje a la cola de ingesta
            channel.basic_publish(
                exchange='',
                routing_key=EDGE_INGEST_QUEUE,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2, # make message persistent
                )
            )
            print(f"Mensaje de datos publicado a '{EDGE_INGEST_QUEUE}': {message.get('user_id', 'N/A')} en {message.get('timestamp', 'N/A')}", file=sys.stderr)
    except Exception as e:
        print(f"Error al publicar mensaje de datos en RabbitMQ: {e}", file=sys.stderr)
    finally:
        if connection:
            connection.close()

def publish_notification_message(user_id: str):
    """
    Publica un mensaje de notificación en la cola de notificación (INGEST_FOG_NOTIFICATION_QUEUE).
    Este mensaje indica que hay nuevos datos para el usuario en la DB.
    """
    connection = None
    try:
        connection = get_rabbitmq_connection()
        if connection:
            channel = connection.channel()
            # Declarar la cola de notificación
            channel.queue_declare(queue=INGEST_FOG_NOTIFICATION_QUEUE, durable=True)
            
            # Publicar el mensaje de notificación (solo el user_id es suficiente)
            notification_message = {"user_id": user_id, "timestamp": datetime.now().isoformat()}
            channel.basic_publish(
                exchange='',
                routing_key=INGEST_FOG_NOTIFICATION_QUEUE,
                body=json.dumps(notification_message),
                properties=pika.BasicProperties(
                    delivery_mode=2, # make message persistent
                )
            )
            print(f"Mensaje de notificación publicado a '{INGEST_FOG_NOTIFICATION_QUEUE}': {user_id}", file=sys.stderr)
    except Exception as e:
        print(f"Error al publicar mensaje de notificación en RabbitMQ: {e}", file=sys.stderr)
    finally:
        if connection:
            connection.close()

def consume_messages(queue_name: str):
    """
    Consume mensajes de una cola específica de RabbitMQ.
    """
    connection = None
    messages = []
    try:
        connection = get_rabbitmq_connection()
        if connection:
            channel = connection.channel()
            # Asegurarse de que la cola existe
            channel.queue_declare(queue=queue_name, durable=True)

            # Configurar el prefetch count para procesar 1 mensaje a la vez
            channel.basic_qos(prefetch_count=1)

            # Consumir mensajes de la cola
            while True:
                method_frame, properties, body = channel.basic_get(queue=queue_name, auto_ack=False)
                if body:
                    message = json.loads(body)
                    messages.append(message)
                    channel.basic_ack(method_frame.delivery_tag) # Reconocer el mensaje
                else:
                    break # No hay más mensajes en este momento

            # print(f"Consumidos {len(messages)} mensajes de la cola '{queue_name}'.", file=sys.stderr)
    except Exception as e:
        print(f"Error al consumir mensajes de RabbitMQ desde la cola '{queue_name}': {e}", file=sys.stderr)
    finally:
        if connection:
            connection.close()
    return messages
