import joblib
import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from app.config import FEATURE_COLUMNS, GENERIC_MODEL_PATH
from app.schemas.ticwatch_schema import TicWatchData

class TicWatchPredictor:
    def __init__(self, model_path: str = None):
        """
        Inicializa el predictor. Si se proporciona un model_path, intenta cargar ese modelo.
        De lo contrario, espera que el modelo se cargue explícitamente más tarde.
        """
        self.model = None
        self.model_path = model_path
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        elif model_path:
            print(f"Advertencia: El modelo en la ruta '{model_path}' no existe al inicializar.")

    def load_model(self, model_path: str):
        """Carga un modelo de Machine Learning desde la ruta especificada."""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"El archivo del modelo no se encontró en: {model_path}")
        try:
            self.model = joblib.load(model_path)
            print(f"Modelo cargado exitosamente desde: {model_path}")
        except Exception as e:
            print(f"Error al cargar el modelo desde {model_path}: {e}")
            self.model = None # Asegurarse de que el modelo es nulo si falla la carga

    def save_model(self, model_path: str):
        """Guarda el modelo actual en la ruta especificada."""
        if self.model is None:
            raise ValueError("No hay un modelo cargado para guardar.")
        
        # Asegurarse de que el directorio exista
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        try:
            joblib.dump(self.model, model_path)
            print(f"Modelo guardado exitosamente en: {model_path}")
        except Exception as e:
            print(f"Error al guardar el modelo en {model_path}: {e}")

    def train_model(self, X: pd.DataFrame, y: pd.Series):
        """
        Entrena un nuevo modelo RandomForestClassifier o re-entrena el existente.
        """
        if self.model is None:
            # Inicializar un nuevo modelo si no hay uno cargado
            self.model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
            print("Inicializando un nuevo RandomForestClassifier para entrenamiento.")
        else:
            print("Re-entrenando el modelo existente (fine-tuning o actualización).")
            # Para RandomForest, "re-entrenar" significa entrenar desde cero con los nuevos datos.
            # No es un fine-tuning incremental como en redes neuronales.
            # Si se quisiera un fine-tuning más real, se necesitaría otro tipo de modelo.
            # Aquí, simplemente se entrena de nuevo con los datos proporcionados.
            
        self.model.fit(X, y)
        print("Modelo entrenado/re-entrenado.")

    def preprocess_data(self, data: TicWatchData) -> pd.DataFrame:
        """
        Pre-procesa los datos crudos del TicWatch en un DataFrame de Pandas
        con las características esperadas por el modelo.
        """
        # Convertir el objeto Pydantic a un diccionario y luego a DataFrame
        # Asegurarse de que el timestamp sea un objeto datetime
        data_dict = data.model_dump() # Usa .model_dump() para Pydantic v2
        
        # Crear un DataFrame con una sola fila
        df = pd.DataFrame([data_dict])
        
        # Seleccionar solo las columnas de características en el orden correcto
        # Asegurarse de que todas las columnas existan, si no, rellenar con 0 o NaN
        processed_df = df[FEATURE_COLUMNS]
        
        return processed_df

    def predict(self, data: TicWatchData) -> str:
        """
        Realiza una predicción sobre el estado de actividad del usuario.
        """
        if self.model is None:
            # Intentar cargar el modelo genérico si no hay ninguno cargado
            if os.path.exists(GENERIC_MODEL_PATH):
                self.load_model(GENERIC_MODEL_PATH)
            else:
                raise ValueError("No hay un modelo cargado y el modelo genérico no existe para predecir.")

        processed_data = self.preprocess_data(data)
        prediction_proba = self.model.predict_proba(processed_data)[0]
        prediction_label = self.model.predict(processed_data)[0]

        return prediction_label