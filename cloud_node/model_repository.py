import os
import joblib
from app.config import MODEL_BASE_DIR, GENERIC_MODEL_PATH

class ModelRepository:
    def __init__(self):
        # Asegurarse de que el directorio base de modelos exista
        os.makedirs(MODEL_BASE_DIR, exist_ok=True)
        print(f"Directorio de modelos: {MODEL_BASE_DIR}")

    def save_model(self, model, model_name: str, is_generic: bool = False):
        """
        Guarda un modelo en el repositorio.
        Si is_generic es True, lo guarda como el modelo genérico.
        De lo contrario, lo guarda en una subcarpeta de modelos personalizados.
        """
        if is_generic:
            path = GENERIC_MODEL_PATH
        else:
            # Para modelos personalizados, usamos el model_name (que será el user_id)
            # y una subcarpeta para organizarlos
            user_model_dir = os.path.join(MODEL_BASE_DIR, "users")
            os.makedirs(user_model_dir, exist_ok=True)
            path = os.path.join(user_model_dir, f"{model_name}.pkl")
        
        joblib.dump(model, path)
        print(f"Modelo '{model_name}' guardado en: {path}")
        return path

    def load_model(self, model_path: str):
        """Carga un modelo desde una ruta específica en el repositorio."""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"El archivo del modelo no se encontró en: {model_path}")
        
        model = joblib.load(model_path)
        print(f"Modelo cargado desde: {model_path}")
        return model

    def get_generic_model_path(self) -> str:
        """Devuelve la ruta al modelo genérico."""
        return GENERIC_MODEL_PATH

    def get_user_model_path(self, user_id: str) -> str:
        """Devuelve la ruta esperada para el modelo personalizado de un usuario."""
        user_model_dir = os.path.join(MODEL_BASE_DIR, "users")
        return os.path.join(user_model_dir, f"{user_id}.pkl")