import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import os

# Importar FEATURE_COLUMNS desde app.config
# GENERIC_MODEL_PATH ya no se usa directamente aquí, ya que el Fog/Edge lo descarga de la API
from app.config import FEATURE_COLUMNS
# Asumo que app.schemas.ticwatch_schema.TicWatchData es una clase Pydantic
from app.schemas.ticwatch_schema import TicWatchData

class TicWatchPredictor:
    def __init__(self, model_path: str = None, model_bytes: bytes = None):
        """
        Inicializa el predictor de TicWatch con un modelo pre-entrenado si se proporciona
        como bytes o desde una ruta local (usado principalmente por el Cloud Trainer).
        Si no se proporciona un modelo, se inicializa con un RandomForestClassifier vacío.

        Args:
            model_path (str): Ruta al archivo del modelo pre-entrenado (principalmente para Cloud Trainer).
            model_bytes (bytes): Bytes del modelo pre-entrenado. Si se proporciona, se
                                 carga en lugar de usar model_path.
        """
        self.model = None

        if model_bytes is not None:
            try:
                # Cargar el modelo desde bytes (usado por Fog/Edge después de descargar de la API)
                self.model = pickle.loads(model_bytes)
                print("TicWatchPredictor: Modelo cargado desde bytes.")
            except Exception as e:
                print(f"Error al cargar el modelo desde bytes: {e}")
                self.model = None
        elif model_path and os.path.exists(model_path):
            try:
                # Cargar el modelo desde una ruta (usado por Cloud Trainer para su almacenamiento local)
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print(f"TicWatchPredictor: Modelo cargado desde la ruta: {model_path}")
            except Exception as e:
                print(f"Error al cargar el modelo desde la ruta {model_path}: {e}")
                self.model = None
        else:
            # Inicializar un nuevo modelo si no se proporciona ninguno
            print("TicWatchPredictor: Inicializando con un nuevo RandomForestClassifier. No se cargó un modelo pre-entrenado.")
            self.model = RandomForestClassifier(random_state=42)

    # Los métodos load_model y save_model han sido eliminados de esta clase.
    # La lógica de cargar/guardar archivos de modelo es responsabilidad de ModelRepository (en Cloud)
    # o de CloudAPIClient (en Fog/Edge, que maneja la descarga/subida de bytes).
    # TicWatchPredictor solo trabaja con el objeto del modelo en memoria o sus bytes.

    def train_model(self, X: pd.DataFrame, y: pd.Series):
        """
        Entrena o re-entrena el modelo con los datos proporcionados.
        Para RandomForest, esto implica re-ajustar el modelo completamente con el nuevo dataset.
        Este método es usado tanto para el re-entrenamiento genérico (Cloud) como para el
        fine-tuning específico de usuario (Fog).
        """
        # Asegurarse de que X contiene solo las columnas de características esperadas
        # Esto es vital para que el modelo entrene con las mismas características que usa para predecir
        X_processed = X[FEATURE_COLUMNS]

        if self.model is None:
            # Si no hay un modelo cargado, crea uno nuevo.
            self.model = RandomForestClassifier(random_state=42)
            print("TicWatchPredictor: Creando un nuevo RandomForestClassifier para el entrenamiento.")
        else:
            print("TicWatchPredictor: Re-ajustando el RandomForestClassifier existente con nuevos datos.")

        self.model.fit(X_processed, y)
        print("TicWatchPredictor: Entrenamiento/fine-tuning del modelo completado.")

    def preprocess_data(self, data: TicWatchData) -> pd.DataFrame:
        """
        Pre-procesa los datos crudos del TicWatch en un DataFrame de Pandas
        con las características esperadas por el modelo.
        """
        # Convertir el objeto Pydantic a un diccionario y luego a DataFrame
        data_dict = data.model_dump() # Usa .model_dump() para Pydantic v2
        
        # Crear un DataFrame con una sola fila
        df = pd.DataFrame([data_dict])
        
        # Seleccionar solo las columnas de características en el orden correcto
        # Asegurarse de que todas las columnas existan, si no, rellenar con 0 o NaN
        # FEATURE_COLUMNS debe estar correctamente definido en app.config
        processed_df = df[FEATURE_COLUMNS]
        
        return processed_df

    def predict(self, data: TicWatchData) -> str:
        """
        Realiza una predicción sobre el estado de actividad del usuario.
        Este método asume que el modelo ya ha sido cargado en la instancia del predictor.
        """
        if self.model is None:
            # En una arquitectura distribuida, el modelo debe ser descargado y
            # pasado al constructor del predictor antes de llamar a predict.
            # No se intenta cargar el modelo genérico directamente aquí.
            raise ValueError("No hay un modelo cargado en el predictor para realizar predicciones.")

        processed_data = self.preprocess_data(data)
        prediction_label = self.model.predict(processed_data)[0]
        # prediction_proba = self.model.predict_proba(processed_data)[0] # Opcional, si necesitas las probabilidades

        return prediction_label

    def get_model_bytes(self) -> bytes:
        """
        Serializa el modelo entrenado a un objeto de bytes.
        Útil para subir el modelo a la Cloud API.
        """
        if self.model is None:
            raise ValueError("No hay un modelo para serializar.")
        return pickle.dumps(self.model)