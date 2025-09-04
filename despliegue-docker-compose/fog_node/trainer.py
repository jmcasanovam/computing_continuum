import time
import json
import os
import pickle # Para serializar/deserializar modelos desde/hacia bytes
from datetime import datetime, timedelta
import pandas as pd
import sys

from app.models.ticwatch_predictor import TicWatchPredictor
from app.data.message_queue import consume_messages, INGEST_FOG_NOTIFICATION_QUEUE
from app.config import FEATURE_COLUMNS
from fog_node.cloud_api_client import CloudAPIClient

# Umbral de datos para disparar el fine-tuning
MIN_SAMPLES_FOR_FINE_TUNING = 20 # Número mínimo de nuevas muestras etiquetadas para un usuario

def process_and_fine_tune_models():
    """
    Procesa los mensajes de la cola de notificación, agrupa los datos por usuario
    y dispara el fine-tuning para usuarios con suficientes datos.
    """
    print(f"[{datetime.now()}] Fog Trainer: Starting to consume messages from '{INGEST_FOG_NOTIFICATION_QUEUE}'...", file=sys.stderr)
    
    # Instanciar el cliente de la Cloud API
    cloud_api_client = CloudAPIClient()

    # 1. Consumir todos los mensajes de la cola de notificación
    raw_notification_messages = consume_messages(INGEST_FOG_NOTIFICATION_QUEUE)

    if not raw_notification_messages:
        print("No new notification messages in the queue. Waiting...", file=sys.stderr)
        return

    print(f"[{datetime.now()}] Fog Trainer: Consumed {len(raw_notification_messages)} notification messages.", file=sys.stderr)

    # Los mensajes de notificación solo contienen user_id y timestamp.
    # Extraer los user_id únicos de los mensajes de notificación
    users_to_process = set()
    for msg in raw_notification_messages:
        user_id = msg.get('user_id')
        if user_id:
            users_to_process.add(user_id)
    
    if not users_to_process:
        print("No valid user IDs found in notification messages. Waiting...", file=sys.stderr)
        return

    print(f"Users with new data to check for fine-tuning: {list(users_to_process)}", file=sys.stderr)

    for user_id in users_to_process: # Iterar sobre los user_id únicos
        # 2. Obtener todos los datos etiquetados para este usuario de la DB central a través de la Cloud API
        # La función get_user_data_from_cloud ya filtra por estado_real IS NOT NULL
        print(f"User {user_id}: Fetching all labeled data from Cloud API...", file=sys.stderr)
        user_training_df = cloud_api_client.get_user_data_from_cloud(user_id)

        if user_training_df.empty or len(user_training_df) < MIN_SAMPLES_FOR_FINE_TUNING:
            print(f"User {user_id}: Not enough labeled data ({len(user_training_df)} samples) or data not fetched. Skipping fine-tuning.", file=sys.stderr)
            continue

        print(f"User {user_id}: Fine-tuning model with {len(user_training_df)} samples.", file=sys.stderr)

        # Preparar datos para el entrenamiento
        X_user = user_training_df[FEATURE_COLUMNS]
        y_user = user_training_df['estado_real']

        # 3. Cargar el modelo actual del usuario (personalizado o genérico) desde la Cloud API
        predictor = None
        current_model_bytes = None
        
        # Primero, intentar descargar el modelo personalizado del usuario
        print(f"User {user_id}: Checking for existing custom model in Cloud API...", file=sys.stderr)
        current_model_bytes = cloud_api_client.download_model(user_id=user_id)

        if current_model_bytes:
            print(f"User {user_id}: Loaded existing custom model from Cloud API.", file=sys.stderr)
            predictor = TicWatchPredictor(model_bytes=current_model_bytes)
        else:
            # Si no hay modelo personalizado, descargar el modelo genérico
            print(f"User {user_id}: No custom model found. Downloading generic model from Cloud API...", file=sys.stderr)
            current_model_bytes = cloud_api_client.download_model(user_id=None) # Descargar genérico

            if current_model_bytes:
                print(f"User {user_id}: Loaded generic model from Cloud API.", file=sys.stderr)
                predictor = TicWatchPredictor(model_bytes=current_model_bytes)
            else:
                print(f"Error: Generic model not found in Cloud API. Cannot fine-tune for user {user_id}.", file=sys.stderr)
                continue # Saltar al siguiente usuario si no hay modelo genérico

        # Si el predictor no se pudo inicializar (ej. problemas con el modelo cargado)
        if predictor is None:
            print(f"Error: Could not initialize predictor for user {user_id}.", file=sys.stderr)
            continue

        # 4. Realizar el fine-tuning
        try:
            predictor.train_model(X_user, y_user) # train_model de RandomForest re-entrena con los nuevos datos

            # 5. Serializar el modelo ajustado a bytes y subirlo a la Cloud API
            updated_model_bytes = pickle.dumps(predictor.model)
            
            print(f"User {user_id}: Uploading fine-tuned model to Cloud API...", file=sys.stderr)
            upload_success = cloud_api_client.upload_user_model(user_id, updated_model_bytes)

            if upload_success:
                update_mapping_success = cloud_api_client.update_user_model_mapping_in_cloud(
                    user_id=user_id,
                    model_path=cloud_api_client.base_url + f"/user/{user_id}",  # Ruta donde se guardará el modelo en la Cloud API
                    model_type="personalized"  # Tipo de modelo personalizado o genérico
                )
                if update_mapping_success:
                    print(f"User {user_id}: Model mapping updated successfully in Cloud API.", file=sys.stderr)
                    print(f"User {user_id}: Fine-tuning and upload complete.", file=sys.stderr)
                else:
                    print(f"User {user_id}: Failed to update model mapping in Cloud API.", file=sys.stderr)
                
            else:
                print(f"User {user_id}: Fine-tuning complete, but failed to upload model to Cloud API.", file=sys.stderr)

        except Exception as e:
            print(f"Error during fine-tuning/upload for user {user_id}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)


def run_fog_trainer_loop(interval_seconds: int = 60):
    """
    Ejecuta el proceso de fine-tuning en un bucle continuo.
    """
    print(f"[{datetime.now()}] Fog Trainer: Starting main loop. Checking for new data every {interval_seconds} seconds.")
    while True:
        process_and_fine_tune_models()
        time.sleep(interval_seconds)

if __name__ == "__main__":
    # Necesario para cargar variables de entorno en el script
    print("Fog Node Trainer: Starting...")
    from dotenv import load_dotenv
    load_dotenv()
    run_fog_trainer_loop(interval_seconds=30)