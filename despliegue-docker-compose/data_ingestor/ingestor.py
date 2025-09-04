import os
import sys
import time
import json
from datetime import datetime

# Importar funciones de la aplicación
from app.data.message_queue import consume_messages, publish_notification_message, EDGE_INGEST_QUEUE, INGEST_FOG_NOTIFICATION_QUEUE
from app.data.database import insert_ticwatch_data # Para insertar en la DB central


def run_data_ingestor_loop(interval_seconds: int = 5):
    """
    Bucle principal del Data Ingestor.
    Consume mensajes de la cola de ingesta, los inserta en la DB,
    y luego publica una notificación al Fog.
    """
    print(f"[{datetime.now()}] Data Ingestor: Starting main loop. Checking for new messages every {interval_seconds} seconds.", file=sys.stderr)

    while True:
        print(f"[{datetime.now()}] Data Ingestor: Attempting to consume messages from '{EDGE_INGEST_QUEUE}'...", file=sys.stderr)
        
        # Consumir mensajes de la cola de ingesta
        # La función consume_messages ya maneja la conexión y el ACK.
        messages = consume_messages(EDGE_INGEST_QUEUE)

        if not messages:
            print(f"[{datetime.now()}] Data Ingestor: No new messages in '{EDGE_INGEST_QUEUE}'. Waiting...", file=sys.stderr)
        else:
            print(f"[{datetime.now()}] Data Ingestor: Consumed {len(messages)} messages from '{EDGE_INGEST_QUEUE}'. Processing...", file=sys.stderr)
            
            # Procesar cada mensaje: insertar en DB y notificar al Fog
            processed_user_ids = set() # Para notificar a cada usuario solo una vez por ciclo
            for message in messages:
                user_id = message.get('user_id')
                timestamp = message.get('timestamp')
                
                if not user_id or not timestamp:
                    print(f"[{datetime.now()}] Data Ingestor: Skipping malformed message: {message}", file=sys.stderr)
                    continue

                print(f"[{datetime.now()}] Data Ingestor: Inserting data for user {user_id} at {timestamp} into DB...", file=sys.stderr)
                
                # Insertar el dato en la base de datos central
                # insert_ticwatch_data ya maneja sus propios reintentos y logs de error.
                try:
                    message['timestamp'] = datetime.fromisoformat(timestamp)  # Asegurar que el timestamp es un objeto datetime
                except ValueError as e:
                    print(f"[{datetime.now()}] Data Ingestor: Error parsing timestamp '{timestamp}' for user {user_id}: {e}", file=sys.stderr)
                    continue
                print(f"[{datetime.now()}] Data Ingestor: Message content: {message}", file=sys.stderr)
                insert_ticwatch_data(message)
                
                # Añadir el user_id al conjunto de procesados para notificar al Fog
                processed_user_ids.add(user_id)
            
            # Publicar una notificación para cada usuario cuyos datos fueron insertados
            for user_id in processed_user_ids:
                print(f"[{datetime.now()}] Data Ingestor: Publishing notification for user {user_id} to '{INGEST_FOG_NOTIFICATION_QUEUE}'...", file=sys.stderr)
                publish_notification_message(user_id) # Notificar al Fog

        # Esperar antes de la siguiente iteración
        time.sleep(interval_seconds)

if __name__ == "__main__":
    print("Data Ingestor Service: Starting...", file=sys.stderr)
    run_data_ingestor_loop(interval_seconds=5) # Intervalo de chequeo más frecuente para ingesta