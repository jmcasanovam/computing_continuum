import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import pika
import json
import time
import random
import sys
from app.data.message_queue import publish_data_message, EDGE_INGEST_QUEUE

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de la Base de Datos
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Configuración de RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS")

def get_db_connection(retries=10, delay=5):
    """Establece una conexión a la DB desde el contenedor con reintentos."""
    conn = None
    for i in range(retries):
        try:
            print(f"Intentando conectar a la DB ({i+1}/{retries})...", file=sys.stderr)
            conn = psycopg2.connect(
                host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
            )
            print("Conexión a la DB exitosa.", file=sys.stderr)
            return conn
        except psycopg2.OperationalError as e:
            print(f"Error operacional al conectar a la DB: {e}. Reintentando en {delay} segundos...", file=sys.stderr)
            time.sleep(delay)
            delay = min(delay * 1.5, 30) # Reducir el factor de aumento para no esperar demasiado
        except Exception as e:
            print(f"Error inesperado al intentar conectar a la DB: {e}", file=sys.stderr)
            return None
    print(f"Falló la conexión a la DB después de {retries} intentos.", file=sys.stderr)
    return None

def get_rabbitmq_connection(retries=15, initial_delay=5, max_delay=60): # Aumentar retries y initial_delay
    """
    Establece una conexión con RabbitMQ utilizando las credenciales del entorno, con reintentos.
    Retorna el objeto de conexión si tiene éxito, None en caso contrario.
    """
    conn = None
    delay = initial_delay
    for i in range(retries):
        try:
            print(f"Intentando conectar a RabbitMQ ({i+1}/{retries})...", file=sys.stderr)
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600
            )
            conn = pika.BlockingConnection(parameters)
            print("Conexión a RabbitMQ exitosa.", file=sys.stderr)
            return conn
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Error operacional al conectar a RabbitMQ: {e}. Reintentando en {delay} segundos...", file=sys.stderr)
            time.sleep(delay)
            delay = min(delay * 1.5, max_delay) # Aumentar el retardo, con un máximo
        except Exception as e:
            print(f"Error inesperado al intentar conectar a RabbitMQ: {e}", file=sys.stderr)
            return None
    print(f"Falló la conexión a RabbitMQ después de {retries} intentos.", file=sys.stderr)
    return None

def insert_sample_ticwatch_data(user_id, num_samples, with_labels=False):
    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            return
        cur = conn.cursor()
        base_time = datetime.now() - timedelta(days=7)
        data_list = []
        possible_states = ["walking", "running", "sleeping", "sedentary"]

        for i in range(num_samples):
            timestamp = base_time + timedelta(seconds=i * 10)
            
            tic_accx = round(random.uniform(-1.0, 1.0), 6)
            tic_accy = round(random.uniform(-1.0, 1.0), 6)
            tic_accz = round(random.uniform(-1.0, 1.0), 6)
            tic_acclx = round(random.uniform(-1.0, 1.0), 6)
            tic_accly = round(random.uniform(-1.0, 1.0), 6)
            tic_acclz = round(random.uniform(-1.0, 1.0), 6)
            tic_girx = round(random.uniform(-1.0, 1.0), 6)
            tic_giry = round(random.uniform(-1.0, 1.0), 6)
            tic_girz = round(random.uniform(-1.0, 1.0), 6)
            tic_hrppg = round(random.uniform(60.0, 180.0), 2)
            tic_step = random.randint(0, 200)
            ticwatchconnected = True
            
            estado_real = random.choice(possible_states) if with_labels else None
            predicted_state = None

            row = (
                user_id,
                f"session_{user_id}_{timestamp.timestamp()}",
                timestamp,
                tic_accx, tic_accy, tic_accz,
                tic_acclx, tic_accly, tic_acclz,
                tic_girx, tic_giry, tic_girz,
                tic_hrppg, tic_step,
                ticwatchconnected,
                estado_real,
                predicted_state
            )
            data_list.append(row)

        query = """
            INSERT INTO ticwatch_data (
                user_id, session_id, timestamp, tic_accx, tic_accy, tic_accz,
                tic_acclx, tic_accly, tic_acclz, tic_girx, tic_giry, tic_girz,
                tic_hrppg, tic_step, ticwatchconnected, estado_real, predicted_state
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        cur.executemany(query, data_list)
        conn.commit()
        print(f"Insertados {len(data_list)} puntos de datos de ejemplo para el usuario {user_id} en la DB (con etiquetas={with_labels}).")
    except Exception as e:
        print(f"Error al insertar datos de ejemplo: {e}", file=sys.stderr)
    finally:
        if conn:
            conn.close()

def publish_sample_message(message: dict):
    """Publica un mensaje de ejemplo en RabbitMQ."""
    connection = None
    try:
        connection = get_rabbitmq_connection()
        if connection:
            channel = connection.channel()
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            channel.basic_publish(
                exchange='',
                routing_key=RABBITMQ_QUEUE,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            print(f"Mensaje publicado en RabbitMQ: {message.get('user_id', 'N/A')} en {message.get('timestamp', 'N/A')}")
    except Exception as e:
        print(f"Error al publicar mensaje en RabbitMQ: {e}", file=sys.stderr)
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    print("Inyectando datos de prueba en la DB y publicando mensajes en RabbitMQ...")
    insert_sample_ticwatch_data('user_test_fog', 30, with_labels=True)

    sample_data_for_queue = {
        "user_id": "user_test_fog",
        "session_id": f"session_user_test_fog_queue_1_{datetime.now().timestamp()}",
        "timestamp": datetime.now().isoformat(),
        "tic_accx": round(random.uniform(-1.0, 1.0), 6),
        "tic_accy": round(random.uniform(-1.0, 1.0), 6),
        "tic_accz": round(random.uniform(-1.0, 1.0), 6),
        "tic_acclx": round(random.uniform(-1.0, 1.0), 6),
        "tic_accly": round(random.uniform(-1.0, 1.0), 6),
        "tic_acclz": round(random.uniform(-1.0, 1.0), 6),
        "tic_girx": round(random.uniform(-1.0, 1.0), 6),
        "tic_giry": round(random.uniform(-1.0, 1.0), 6),
        "tic_girz": round(random.uniform(-1.0, 1.0), 6),
        "tic_hrppg": round(random.uniform(60.0, 180.0), 2),
        "tic_step": random.randint(0, 200),
        "ticwatchconnected": True,
        "estado_real": "walking",
        "predicted_state": None
    }
    publish_data_message(sample_data_for_queue)

    sample_data_for_queue_2 = {
        "user_id": "user_test_fog",
        "session_id": f"session_user_test_fog_queue_2_{datetime.now().timestamp()}",
        "timestamp": (datetime.now() - timedelta(seconds=10)).isoformat(),
        "tic_accx": round(random.uniform(-1.0, 1.0), 6),
        "tic_accy": round(random.uniform(-1.0, 1.0), 6),
        "tic_accz": round(random.uniform(-1.0, 1.0), 6),
        "tic_acclx": round(random.uniform(-1.0, 1.0), 6),
        "tic_accly": round(random.uniform(-1.0, 1.0), 6),
        "tic_acclz": round(random.uniform(-1.0, 1.0), 6),
        "tic_girx": round(random.uniform(-1.0, 1.0), 6),
        "tic_giry": round(random.uniform(-1.0, 1.0), 6),
        "tic_girz": round(random.uniform(-1.0, 1.0), 6),
        "tic_hrppg": round(random.uniform(60.0, 180.0), 2),
        "tic_step": random.randint(0, 200),
        "ticwatchconnected": True,
        "estado_real": "running",
        "predicted_state": None
    }

    publish_data_message(sample_data_for_queue_2)
    

    print("\nRevisa los logs del Fog Trainer. Debería procesar los mensajes e intentar el fine-tuning.")
    print("Si todo va bien, deberías ver que se han insertado los datos en la DB y se han publicado los mensajes en RabbitMQ.")