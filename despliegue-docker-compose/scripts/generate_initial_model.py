import os
from datetime import datetime, timedelta
import pandas as pd
import sys # Importar sys para stderr
import random # <--- ¡IMPORTANTE: Añadir esta importación!

from app.models.ticwatch_predictor import TicWatchPredictor
from app.data.database import create_tables, insert_ticwatch_data, get_all_training_data
from app.config import GENERIC_MODEL_PATH, FEATURE_COLUMNS, MODELS_DIR
from cloud_node.model_repository import ModelRepository

def generate_initial_model():
    print("--- generate_initial_model: Starting initial model generation ---", file=sys.stderr)

    # 1. Asegurarse de que el directorio de modelos exista
    try:
        os.makedirs(MODELS_DIR, exist_ok=True)
        print(f"Ensured models directory exists at: {MODELS_DIR}", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: Could not create models directory {MODELS_DIR}: {e}", file=sys.stderr)
        sys.exit(1) # Salir si no se puede crear el directorio

    # 2. Generar datos dummy
    print("Generating dummy data for initial model...", file=sys.stderr)
    dummy_data = []
    # Inicia 30 días en el pasado para tener un rango de tiempo
    start_time = datetime.now() - timedelta(days=30)
    user_id = "initial_generic_user"
    session_id_base = "initial_session_"

    activities = ["sleeping", "sedentary", "training"]
    num_samples_per_activity = 1000

    for activity in activities:
        for i in range(num_samples_per_activity):
            session_id = f"{session_id_base}{activity}_{i}"
            
            # Aseguramos que el timestamp tenga formato YYYY-MM-DD HH:MM:SS
            # Añade minutos y segundos para asegurar la parte de la hora y variedad
            current_time = start_time + timedelta(minutes=i*random.randint(1, 5), seconds=random.randint(0, 59))
            
            # --- CAMBIO CLAVE AQUÍ: Usar strftime para forzar el formato exacto ---
            timestamp_str = current_time.strftime('%Y-%m-%d %H:%M:%S') 
            
            data_point = {
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": timestamp_str, # Usar el string formateado
                "tic_accx": random.uniform(-1, 1), # Valores aleatorios para las características
                "tic_accy": random.uniform(-1, 1),
                "tic_accz": random.uniform(-1, 1),
                "tic_acclx": random.uniform(-1, 1),
                "tic_accly": random.uniform(-1, 1),
                "tic_acclz": random.uniform(-1, 1),
                "tic_girx": random.uniform(-1, 1),
                "tic_giry": random.uniform(-1, 1),
                "tic_girz": random.uniform(-1, 1),
                "tic_hrppg": random.uniform(60, 120),
                "tic_step": random.randint(0, 100),
                "ticwatchconnected": True,
                "predicted_state": None,
                "estado_real": activity # Asignar la actividad como etiqueta real
            }
            dummy_data.append(data_point)

    print(f"Generated {len(dummy_data)} dummy data points.", file=sys.stderr)

    # 3. Insertar datos dummy en la base de datos
    print("Inserting dummy data into the database...", file=sys.stderr)
    for data_point in dummy_data:
        try:
            insert_ticwatch_data(data_point)
        except Exception as e:
            print(f"ERROR inserting dummy data point: {data_point}. Error: {e}", file=sys.stderr)
            sys.exit(1)
    print("Dummy data inserted into the database.", file=sys.stderr)

    # 4. Recuperar datos para entrenar el modelo inicial
    print("Retrieving all labeled data from DB for initial model training...", file=sys.stderr)
    try:
        training_data = get_all_training_data()
    except Exception as e:
        print(f"ERROR retrieving training data: {e}", file=sys.stderr)
        sys.exit(1)

    if training_data.empty:
        print("ERROR: No data found in DB for initial model training after insertion. Cannot generate initial model.", file=sys.stderr)
        sys.exit(1)

    print(f"Retrieved {len(training_data)} data points for initial model training.", file=sys.stderr)

    X_initial = training_data[FEATURE_COLUMNS]
    y_initial = training_data['estado_real']

    print("Initializing TicWatchPredictor and training initial model...", file=sys.stderr)
    predictor = TicWatchPredictor()
    try:
        predictor.train_model(X_initial, y_initial)
        print("Initial model trained.", file=sys.stderr)
    except Exception as e:
        print(f"ERROR during initial model training: {e}", file=sys.stderr)
        sys.exit(1)

    # 5. Guardar el modelo inicial
    print(f"Saving initial generic model to: {GENERIC_MODEL_PATH}", file=sys.stderr)
    model_repo = ModelRepository()
    try:
        model_repo.save_model(predictor.model, "generic_activity_model", is_generic=True)
        print(f"Initial generic model successfully saved to {GENERIC_MODEL_PATH}", file=sys.stderr)
    except Exception as e:
        print(f"ERROR saving initial generic model: {e}", file=sys.stderr)
        sys.exit(1) # Salir si falla el guardado del modelo

    print("--- generate_initial_model: Initial model generation complete ---", file=sys.stderr)

if __name__ == "__main__":
    print("Running generate_initial_model directly (for testing purposes only).", file=sys.stderr)
    generate_initial_model()