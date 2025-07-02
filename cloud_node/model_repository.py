import os
import pickle
import sys
from app.config import MODELS_DIR, GENERIC_MODEL_PATH, USER_MODELS_DIR # Importamos USER_MODELS_DIR

class ModelRepository:
    def __init__(self):
        try:
            os.makedirs(MODELS_DIR, exist_ok=True)
            os.makedirs(USER_MODELS_DIR, exist_ok=True) # Asegurarse de que el directorio de usuarios exista
            print(f"ModelRepository initialized. MODELS_DIR: {MODELS_DIR}, USER_MODELS_DIR: {USER_MODELS_DIR}", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Failed to create model directories: {e}", file=sys.stderr)

    def save_model(self, model, model_name: str, user_id: str = None, is_generic: bool = False) -> str:
        """
        Guarda un modelo entrenado en disco.
        Si is_generic es True, lo guarda en el directorio de modelos genéricos.
        Si se proporciona user_id, lo guarda en el directorio de modelos específicos del usuario.
        """
        if is_generic:
            save_path = GENERIC_MODEL_PATH
        elif user_id:
            user_model_dir = os.path.join(USER_MODELS_DIR, user_id) # Usar USER_MODELS_DIR aquí
            try:
                os.makedirs(user_model_dir, exist_ok=True)
            except Exception as e:
                print(f"ERROR: Could not create user model directory {user_model_dir}: {e}", file=sys.stderr)
                raise

            save_path = os.path.join(user_model_dir, f"{model_name}.pkl")
        else:
            raise ValueError("Must provide either user_id or set is_generic to True.")

        print(f"Attempting to save model to: {save_path}", file=sys.stderr)
        try:
            with open(save_path, 'wb') as f:
                pickle.dump(model, f)
            print(f"Model successfully written to {save_path}", file=sys.stderr)
            return save_path
        except Exception as e:
            print(f"ERROR: Failed to save model to {save_path}: {e}", file=sys.stderr)
            raise

    def load_model(self, model_path: str):
        """Carga un modelo desde una ruta dada."""
        print(f"Attempting to load model from: {model_path}", file=sys.stderr)
        if not os.path.exists(model_path):
            print(f"ERROR: Model file not found at {model_path}", file=sys.stderr)
            return None
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            print(f"Model successfully loaded from {model_path}", file=sys.stderr)
            return model
        except Exception as e:
            print(f"ERROR: Failed to load model from {model_path}: {e}", file=sys.stderr)
            return None

    def get_generic_model_path(self) -> str:
        """Devuelve la ruta al modelo genérico."""
        return GENERIC_MODEL_PATH

    def get_user_model_path(self, user_id: str) -> str:
        """Devuelve la ruta esperada para el modelo personalizado de un usuario."""
        # CAMBIO CLAVE AQUÍ: Usar USER_MODELS_DIR en lugar de MODEL_BASE_DIR
        user_model_dir = os.path.join(USER_MODELS_DIR, user_id)
        # La convención es que el nombre del archivo pkl del modelo de usuario sea el user_id
        return os.path.join(user_model_dir, f"{user_id}.pkl")