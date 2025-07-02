import time
from datetime import datetime
import pandas as pd
import os

from app.models.ticwatch_predictor import TicWatchPredictor
from app.data.database import get_all_training_data, create_tables, update_user_model_mapping
from app.config import FEATURE_COLUMNS, GENERIC_MODEL_PATH
from cloud_node.model_repository import ModelRepository

# Umbral de datos para disparar el re-entrenamiento del modelo genérico
# Podría ser un número de nuevas muestras desde el último entrenamiento,
# o un número total de muestras, o basado en la calidad del modelo.
MIN_GLOBAL_SAMPLES_FOR_RETRAIN = 500 # Un valor de ejemplo

def retrain_generic_model():
    """
    Carga todos los datos etiquetados de la base de datos,
    re-entrena el modelo genérico y lo guarda.
    """
    print(f"[{datetime.now()}] Cloud Trainer: Iniciando el re-entrenamiento del modelo genérico.")

    # 1. Cargar todos los datos con etiquetas de verdad
    print("Cargando todos los datos de entrenamiento con etiquetas de verdad desde la DB...")
    all_labeled_data = get_all_training_data()

    if all_labeled_data.empty:
        print("No hay datos etiquetados disponibles para entrenar el modelo genérico. Abortando.")
        return

    # Opcional: Podrías añadir una lógica aquí para verificar si hay "suficientes" datos nuevos
    # desde la última vez que se entrenó el modelo genérico, o si el rendimiento ha bajado.
    if len(all_labeled_data) < MIN_GLOBAL_SAMPLES_FOR_RETRAIN:
        print(f"Número de muestras globales ({len(all_labeled_data)}) por debajo del umbral ({MIN_GLOBAL_SAMPLES_FOR_RETRAIN}). Saltando re-entrenamiento.")
        return

    X_global = all_labeled_data[FEATURE_COLUMNS]
    y_global = all_labeled_data['estado_real']

    print(f"Datos cargados para entrenamiento global: {len(X_global)} muestras.")
    print(f"Distribución global de clases: \n{y_global.value_counts()}")

    # 2. Entrenar (o re-entrenar) el modelo genérico
    # Se inicializa un nuevo predictor que no carga ningún modelo por defecto,
    # ya que vamos a entrenar uno nuevo.
    predictor = TicWatchPredictor()
    predictor.train_model(X_global, y_global)

    # 3. Guardar el nuevo modelo genérico
    model_repo = ModelRepository()
    new_generic_model_path = model_repo.save_model(predictor.model, "generic_activity_model", is_generic=True)
    
    # Opcional: Actualizar el mapeo de los usuarios que aún usan el modelo genérico
    # Esto es una simplificación; en un sistema real, los Edge Nodes
    # podrían tener un mecanismo para "refrescar" su modelo genérico cacheado,
    # o podrías actualizar explícitamente los mapeos de los usuarios que usan "generic".
    # Por ahora, simplemente sobrescribimos el archivo del modelo genérico.
    # Los Edge Nodes lo recargarán cuando lo necesiten (por ejemplo, al iniciar un nuevo proceso
    # de inferencia para un usuario nuevo o cuando el modelo actual no sea el genérico).

    print(f"[{datetime.now()}] Cloud Trainer: Modelo genérico re-entrenado y guardado en: {new_generic_model_path}")

def run_cloud_trainer_loop(interval_hours: int = 24):
    """
    Ejecuta el proceso de re-entrenamiento del modelo genérico en un bucle continuo.
    """

    print(f"[{datetime.now()}] Cloud Trainer: Iniciando bucle principal. Verificando datos cada {interval_hours} horas.")
    while True:
        retrain_generic_model()
        time.sleep(interval_hours * 3600) # Convertir horas a segundos

if __name__ == "__main__":
    # Asegurarse de que el directorio de la base de datos exista antes de cualquier operación
    from app.config import DATABASE_URL
    db_dir = os.path.dirname(DATABASE_URL)
    os.makedirs(db_dir, exist_ok=True)
    
    # Este script también puede ser el punto de entrada para la creación inicial de tablas
    create_tables() 
    
    # El modelo genérico inicial se genera con scripts/generate_initial_model.py
    # Este trainer de la nube es para los re-entrenamientos posteriores.
    
    run_cloud_trainer_loop(interval_hours=1) # Para pruebas, re-entrenar cada hora