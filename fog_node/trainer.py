import time
import json
import os
from datetime import datetime, timedelta
import pandas as pd

from app.models.ticwatch_predictor import TicWatchPredictor
from app.data.database import get_user_data, update_user_model_mapping, insert_ticwatch_data, get_user_model_mapping
from app.data.message_queue import consume_messages
from app.config import FEATURE_COLUMNS
from cloud_node.model_repository import ModelRepository

# Umbral de datos para disparar el fine-tuning
MIN_SAMPLES_FOR_FINE_TUNING = 20 # Número mínimo de nuevas muestras etiquetadas para un usuario

def process_and_fine_tune_models():
    """
    Procesa los mensajes de la cola, agrupa los datos por usuario
    y dispara el fine-tuning para usuarios con suficientes datos.
    """
    print(f"[{datetime.now()}] Fog Trainer: Starting to consume messages...")
    
    # 1. Consumir todos los mensajes de la cola
    raw_messages = consume_messages()
    
    if not raw_messages:
        print("No new messages in the queue. Waiting...")
        return

    print(f"[{datetime.now()}] Fog Trainer: Consumed {len(raw_messages)} messages.")

    # Convertir mensajes a DataFrame de Pandas para fácil manipulación
    # Asegurarse de que 'timeStamp' se convierta a datetime si viene como string
    df_messages = pd.DataFrame(raw_messages)
    df_messages['timeStamp'] = pd.to_datetime(df_messages['timeStamp'])

    # Opcional: Insertar los mensajes en la DB central si no se hizo asíncronamente desde el Edge
    # En nuestro diseño, ya se insertan desde el Edge. Esto sería un reaseguro.
    # for _, row in df_messages.iterrows():
    #     insert_ticwatch_data(row.to_dict())

    # 2. Agrupar datos por usuario y filtrar los que tienen etiquetas de verdad
    # Filtrar solo los datos que tienen 'estado_real' (etiqueta de verdad)
    labeled_data = df_messages[df_messages['estado_real'].notna()]
    
    if labeled_data.empty:
        print("No new labeled data found in consumed messages. Waiting...")
        return

    users_with_new_labeled_data = labeled_data['user_id'].unique()
    print(f"Users with new labeled data: {users_with_new_labeled_data}")

    model_repo = ModelRepository()

    for user_id in users_with_new_labeled_data:
        # Obtener todos los datos etiquetados para este usuario de la DB central
        # Se asume que la DB central tiene todos los datos históricos, incluyendo los nuevos de la cola
        user_training_df = get_user_data(user_id) # Esta función ya filtra por user_id y esperamos 'estado_real'
        
        # Filtrar solo las filas con 'estado_real' no nulo para el entrenamiento
        user_training_df = user_training_df[user_training_df['estado_real'].notna()]

        if len(user_training_df) < MIN_SAMPLES_FOR_FINE_TUNING:
            print(f"User {user_id}: Not enough labeled data ({len(user_training_df)} samples). Skipping fine-tuning.")
            continue

        print(f"User {user_id}: Fine-tuning model with {len(user_training_df)} samples.")
        
        # Preparar datos para el entrenamiento
        X_user = user_training_df[FEATURE_COLUMNS]
        y_user = user_training_df['estado_real']

        # 3. Cargar el modelo actual del usuario (personalizado o genérico)
        current_user_model_info = get_user_model_mapping(user_id)
        current_model_path = None
        
        if current_user_model_info and os.path.exists(current_user_model_info['model_path']):
            current_model_path = current_user_model_info['model_path']
            print(f"User {user_id}: Loading existing custom model from {current_model_path}")
        else:
            # Si no hay modelo personalizado o no se encuentra, usar el modelo genérico
            current_model_path = model_repo.get_generic_model_path()
            print(f"User {user_id}: No custom model found or path invalid. Loading generic model from {current_model_path}")
            if not os.path.exists(current_model_path):
                print(f"Error: Generic model not found at {current_model_path}. Cannot fine-tune.")
                continue # Saltar al siguiente usuario si el modelo genérico no existe

        predictor = TicWatchPredictor(model_path=current_model_path)
        
        # 4. Realizar el fine-tuning
        try:
            predictor.train_model(X_user, y_user) # train_model de RandomForest re-entrena con los nuevos datos
            
            # 5. Guardar el modelo personalizado actualizado
            new_model_path = model_repo.save_model(predictor.model, user_id, is_generic=False)
            
            # 6. Actualizar el mapeo de usuario a modelo en la DB central
            update_user_model_mapping(user_id, new_model_path, "personalizado")
            print(f"User {user_id}: Fine-tuning complete. New model saved and mapped: {new_model_path}")

        except Exception as e:
            print(f"Error during fine-tuning for user {user_id}: {e}")

def run_fog_trainer_loop(interval_seconds: int = 60):
    """
    Ejecuta el proceso de fine-tuning en un bucle continuo.
    """

    print(f"[{datetime.now()}] Fog Trainer: Starting main loop. Checking for new data every {interval_seconds} seconds.")
    while True:
        process_and_fine_tune_models()
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_fog_trainer_loop(interval_seconds=30) # Comprueba cada 30 segundos