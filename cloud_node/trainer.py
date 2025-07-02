import time
from datetime import datetime
import pandas as pd
import os
import sys # Importar sys

from app.models.ticwatch_predictor import TicWatchPredictor
from app.data.database import get_all_training_data, create_tables, update_user_model_mapping
from app.config import FEATURE_COLUMNS, GENERIC_MODEL_PATH
from cloud_node.model_repository import ModelRepository

MIN_GLOBAL_SAMPLES_FOR_RETRAIN = 500

def retrain_generic_model():
    print(f"[{datetime.now()}] Cloud Trainer: Iniciando el re-entrenamiento del modelo genérico.", file=sys.stderr)

    print("Cargando todos los datos de entrenamiento con etiquetas de verdad desde la DB...", file=sys.stderr)
    try:
        all_labeled_data = get_all_training_data()
    except Exception as e:
        print(f"ERROR: Failed to get all training data: {e}", file=sys.stderr)
        return pd.DataFrame() # Return empty DataFrame on error

    if all_labeled_data.empty:
        print("No hay datos etiquetados disponibles para entrenar el modelo genérico. Abortando.", file=sys.stderr)
        return

    if len(all_labeled_data) < MIN_GLOBAL_SAMPLES_FOR_RETRAIN:
        print(f"Número de muestras globales ({len(all_labeled_data)}) por debajo del umbral ({MIN_GLOBAL_SAMPLES_FOR_RETRAIN}). Saltando re-entrenamiento.", file=sys.stderr)
        return

    X_global = all_labeled_data[FEATURE_COLUMNS]
    y_global = all_labeled_data['estado_real']

    print(f"Datos cargados para entrenamiento global: {len(X_global)} muestras.", file=sys.stderr)
    print(f"Distribución global de clases: \n{y_global.value_counts()}", file=sys.stderr)

    predictor = TicWatchPredictor()
    try:
        predictor.train_model(X_global, y_global)
        print("Modelo genérico entrenado. Guardando...", file=sys.stderr)
        model_repo = ModelRepository()
        new_generic_model_path = model_repo.save_model(predictor.model, "generic_activity_model", is_generic=True)
        print(f"[{datetime.now()}] Cloud Trainer: Modelo genérico re-entrenado y guardado en: {new_generic_model_path}", file=sys.stderr)
    except Exception as e:
        print(f"ERROR durante el entrenamiento o guardado del modelo genérico: {e}", file=sys.stderr)
        # No sys.exit(1) aquí, ya que queremos que el bucle continúe si es un problema temporal.

def run_cloud_trainer_loop(interval_hours: int = 24):

    print(f"[{datetime.now()}] Cloud Trainer: Iniciando bucle principal. Verificando datos cada {interval_hours} horas.", file=sys.stderr)
    while True:
        print(f"[{datetime.now()}] Cloud Trainer: Running periodic re-training check...", file=sys.stderr)
        retrain_generic_model()
        print(f"[{datetime.now()}] Cloud Trainer: Periodic re-training check complete. Sleeping for {interval_hours} hours.", file=sys.stderr)
        time.sleep(interval_hours * 3600)

if __name__ == "__main__":
    # Esta parte solo se ejecutaría si se ejecuta trainer.py directamente,
    # no a través de run_cloud_trainer_init_and_loop.py.
    # La inicialización ya se maneja en run_cloud_trainer_init_and_loop.py.
    run_cloud_trainer_loop(interval_hours=1)