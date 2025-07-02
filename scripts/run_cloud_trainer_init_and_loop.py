import os
from app.config import GENERIC_MODEL_PATH, DATABASE_URL
from scripts.generate_initial_model import generate_initial_model
from app.data.database import create_tables
from cloud_node.trainer import run_cloud_trainer_loop # Importa la función del bucle del trainer

def ensure_initialization():
    """
    Asegura que la base de datos y el modelo genérico inicial existan.
    Si no, los genera.
    """
    print("Cloud Trainer Init: Ensuring database tables are created...")
    # Asegurarse de que el directorio de la base de datos exista
    db_dir = os.path.dirname(DATABASE_URL)
    os.makedirs(db_dir, exist_ok=True)
    create_tables()
    print("Cloud Trainer Init: Database tables checked.")

    if not os.path.exists(GENERIC_MODEL_PATH):
        print(f"Cloud Trainer Init: Generic model not found at {GENERIC_MODEL_PATH}. Generating initial model...")
        generate_initial_model()
        print("Cloud Trainer Init: Initial generic model generated.")
    else:
        print(f"Cloud Trainer Init: Generic model already exists at {GENERIC_MODEL_PATH}. Skipping initial generation.")

if __name__ == "__main__":
    ensure_initialization()
    print("Cloud Trainer Init: Initial setup complete. Starting main training loop.")
    run_cloud_trainer_loop(interval_hours=1) # O el intervalo que desees para el re-entrenamiento periódico