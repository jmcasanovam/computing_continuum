import time
import json
import os
import pickle # Para serializar/deserializar modelos desde/hacia bytes
from datetime import datetime, timedelta
import pandas as pd

from app.models.ticwatch_predictor import TicWatchPredictor
from app.data.message_queue import consume_messages
from app.config import FEATURE_COLUMNS
from fog_node.cloud_api_client import CloudAPIClient

# Umbral de datos para disparar el fine-tuning
MIN_SAMPLES_FOR_FINE_TUNING = 20 # Número mínimo de nuevas muestras etiquetadas para un usuario

def process_and_fine_tune_models():
    """
    Procesa los mensajes de la cola, agrupa los datos por usuario
    y dispara el fine-tuning para usuarios con suficientes datos.
    """
    print(f"[{datetime.now()}] Fog Trainer: Starting to consume messages...")

    # Instanciar el cliente de la Cloud API
    cloud_api_client = CloudAPIClient()

    # 1. Consumir todos los mensajes de la cola
    raw_messages = consume_messages()

    if not raw_messages:
        print("No new messages in the queue. Waiting...")
        return

    print(f"[{datetime.now()}] Fog Trainer: Consumed {len(raw_messages)} messages.")

    # Convertir mensajes a DataFrame de Pandas para fácil manipulación
    df_messages = pd.DataFrame(raw_messages)
    # Convertir 'timeStamp' a datetime si no lo es ya
    if 'timeStamp' in df_messages.columns:
        df_messages['timeStamp'] = pd.to_datetime(df_messages['timeStamp'])
    # Asegurarse de que 'user_id' es un string para las operaciones
    if 'user_id' in df_messages.columns:
        df_messages['user_id'] = df_messages['user_id'].astype(str)

    # 2. Agrupar datos por usuario y filtrar los que tienen etiquetas de verdad
    labeled_data = df_messages[df_messages['estado_real'].notna()]

    if labeled_data.empty:
        print("No new labeled data found in consumed messages. Waiting...")
        return

    users_with_new_labeled_data = labeled_data['user_id'].unique()
    print(f"Users with new labeled data: {users_with_new_labeled_data}")

    for user_id in users_with_new_labeled_data:
        # Obtener todos los datos etiquetados para este usuario de la DB central a través de la Cloud API
        print(f"User {user_id}: Fetching all labeled data from Cloud API...")
        user_training_df = cloud_api_client.get_user_data_from_cloud(user_id) # Usar el cliente

        if user_training_df.empty or len(user_training_df) < MIN_SAMPLES_FOR_FINE_TUNING:
            print(f"User {user_id}: Not enough labeled data ({len(user_training_df)} samples) or data not fetched. Skipping fine-tuning.")
            continue

        print(f"User {user_id}: Fine-tuning model with {len(user_training_df)} samples.")

        # Preparar datos para el entrenamiento
        X_user = user_training_df[FEATURE_COLUMNS]
        y_user = user_training_df['estado_real']

        # 3. Cargar el modelo actual del usuario (personalizado o genérico) desde la Cloud API
        predictor = None
        current_model_bytes = None
        
        # Primero, intentar descargar el modelo personalizado del usuario
        print(f"User {user_id}: Checking for existing custom model in Cloud API...")
        current_model_bytes = cloud_api_client.download_model(user_id=user_id)

        if current_model_bytes:
            print(f"User {user_id}: Loaded existing custom model from Cloud API.")
            predictor = TicWatchPredictor(model_bytes=current_model_bytes)
        else:
            # Si no hay modelo personalizado, descargar el modelo genérico
            print(f"User {user_id}: No custom model found. Downloading generic model from Cloud API...")
            current_model_bytes = cloud_api_client.download_model(user_id=None) # Descargar genérico

            if current_model_bytes:
                print(f"User {user_id}: Loaded generic model from Cloud API.")
                predictor = TicWatchPredictor(model_bytes=current_model_bytes)
            else:
                print(f"Error: Generic model not found in Cloud API. Cannot fine-tune for user {user_id}.")
                continue # Saltar al siguiente usuario si no hay modelo genérico

        # Si el predictor no se pudo inicializar (ej. problemas con el modelo cargado)
        if predictor is None:
            print(f"Error: Could not initialize predictor for user {user_id}.")
            continue

        # 4. Realizar el fine-tuning
        try:
            predictor.train_model(X_user, y_user) # train_model de RandomForest re-entrena con los nuevos datos

            # 5. Serializar el modelo ajustado a bytes y subirlo a la Cloud API
            # TicWatchPredictor debería tener un método para obtener el modelo subyacente
            updated_model_bytes = pickle.dumps(predictor.model) # Asumiendo que predictor.model es el objeto de Scikit-learn
            
            print(f"User {user_id}: Uploading fine-tuned model to Cloud API...")
            upload_success = cloud_api_client.upload_user_model(user_id, updated_model_bytes)

            if upload_success:
                update_mapping_success = cloud_api_client.update_user_model_mapping_in_cloud(
                    user_id=user_id,
                    model_path=cloud_api_client.base_url + f"/user/{user_id}",  # Ruta donde se guardará el modelo en la Cloud API
                    model_type="personalized"  # Tipo de modelo personalizado o genérico
                )
                if update_mapping_success:
                    print(f"User {user_id}: Model mapping updated successfully in Cloud API.")
                    print(f"User {user_id}: Fine-tuning and upload complete.")
                else:
                    print(f"User {user_id}: Failed to update model mapping in Cloud API.")
                
            else:
                print(f"User {user_id}: Fine-tuning complete, but failed to upload model to Cloud API.")

        except Exception as e:
            print(f"Error during fine-tuning/upload for user {user_id}: {e}")

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
    from dotenv import load_dotenv
    load_dotenv()
    run_fog_trainer_loop(interval_seconds=30)