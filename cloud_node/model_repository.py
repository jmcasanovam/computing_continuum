import os
import pickle
from app.config import GENERIC_MODEL_PATH, USER_MODELS_DIR, MODELS_DIR

class ModelRepository:
    def __init__(self):
        self.models_dir = MODELS_DIR # Ruta base para todos los modelos
        self.generic_model_path = GENERIC_MODEL_PATH
        self.user_models_dir = USER_MODELS_DIR
        # Asegurarse de que los directorios existen al inicializar
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.user_models_dir, exist_ok=True)
        print(f"ModelRepository initialized. MODELS_DIR: {self.models_dir}")

    def get_generic_model_path(self):
        return self.generic_model_path

    def get_user_model_path(self, user_id: str):
        return os.path.join(self.user_models_dir, f'{user_id}_activity_model.pkl')

    def save_model(self, model, identifier: str, is_generic: bool = True):
        path = self.get_generic_model_path() if is_generic else self.get_user_model_path(identifier)
        try:
            with open(path, 'wb') as f:
                pickle.dump(model, f)
            print(f"Model successfully written to {path}")
            return path
        except Exception as e:
            print(f"Error writing model to {path}: {e}")
            raise

    def load_model(self, identifier: str, is_generic: bool = True):
        path = self.get_generic_model_path() if is_generic else self.get_user_model_path(identifier)
        if not os.path.exists(path):
            print(f"Model not found at {path}")
            return None
        try:
            with open(path, 'rb') as f:
                model = pickle.load(f)
            print(f"Model successfully loaded from {path}")
            return model
        except Exception as e:
            print(f"Error loading model from {path}: {e}")
            return None