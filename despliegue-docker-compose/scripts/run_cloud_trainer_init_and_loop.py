import os
import sys # Importar sys para manejar errores
from app.config import GENERIC_MODEL_PATH, DATABASE_URL
from scripts.generate_initial_model import generate_initial_model
from app.data.database import create_tables
from cloud_node.trainer import run_cloud_trainer_loop

def ensure_initialization():
    print("--- Cloud Trainer Init: Starting Initialization Process ---", file=sys.stderr)
    print(f"Checking for DB directory: {os.path.dirname(DATABASE_URL)}", file=sys.stderr)
    db_dir = os.path.dirname(DATABASE_URL)
    os.makedirs(db_dir, exist_ok=True)
    print("Cloud Trainer Init: Ensuring database tables are created...", file=sys.stderr)
    try:
        create_tables()
        print("Cloud Trainer Init: Database tables checked.", file=sys.stderr)
    except Exception as e:
        print(f"ERROR during create_tables: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Checking for generic model at: {GENERIC_MODEL_PATH}", file=sys.stderr)
    if not os.path.exists(GENERIC_MODEL_PATH):
        print(f"Cloud Trainer Init: Generic model not found. Generating initial model...", file=sys.stderr)
        try:
            generate_initial_model()
            print("Cloud Trainer Init: Initial generic model generated.", file=sys.stderr)
        except Exception as e:
            print(f"ERROR during generate_initial_model: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Cloud Trainer Init: Generic model already exists. Skipping initial generation.", file=sys.stderr)
    print("--- Cloud Trainer Init: Initialization Process Complete ---", file=sys.stderr)

if __name__ == "__main__":
    print("--- cloud_trainer_init_and_loop.py START ---", file=sys.stderr)
    try:
        ensure_initialization()
        print("Cloud Trainer Init: Initial setup complete. Starting main training loop.", file=sys.stderr)
        run_cloud_trainer_loop(interval_hours=1)
    except Exception as e:
        print(f"FATAL ERROR in main loop of cloud_trainer_init_and_loop.py: {e}", file=sys.stderr)
        sys.exit(1)