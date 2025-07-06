import requests
import os
import json
import io # Para manejar datos binarios como archivos en memoria
import pandas as pd # Necesario para pd.DataFrame en get_user_data_from_cloud
# Importar la configuración centralizada
from app.config import CLOUD_API_HOST, CLOUD_API_PORT

class CloudAPIClient:
    def __init__(self):
        self.base_url = f"http://{CLOUD_API_HOST}:{CLOUD_API_PORT}/models"
        self.data_url = f"http://{CLOUD_API_HOST}:{CLOUD_API_PORT}/data" # Nueva URL base para datos
        self.users_url = f"http://{CLOUD_API_HOST}:{CLOUD_API_PORT}/users" # Nueva URL base para usuarios (mapeo de modelos)
        print(f"CloudAPIClient initialized. Models URL: {self.base_url}, Data URL: {self.data_url}, Users URL: {self.users_url}")


    def download_model(self, user_id: str = None):
        """
        Descarga el modelo genérico o un modelo de usuario específico de la Cloud API.
        Retorna los bytes del modelo si tiene éxito, None en caso contrario.
        """
        if user_id:
            url = f"{self.base_url}/user/{user_id}"
            model_type = f"user {user_id}"
        else:
            url = f"{self.base_url}/generic"
            model_type = "generic"

        try:
            print(f"Attempting to download {model_type} model from {url}...")
            response = requests.get(url, stream=True) # stream=True para descargar archivos grandes
            response.raise_for_status() # Lanza HTTPError para respuestas 4xx/5xx

            # Leer el contenido del archivo en un buffer de Bytes
            model_bytes = io.BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                model_bytes.write(chunk)
            model_bytes.seek(0) # Rebobinar el buffer al inicio

            print(f"Successfully downloaded {model_type} model.")
            return model_bytes.getvalue() # Retorna los bytes brutos del modelo
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {model_type} model from {url}: {e}")
            return None

    def upload_user_model(self, user_id: str, model_bytes: bytes):
        """
        Sube un modelo de usuario a la Cloud API.
        model_bytes debe ser los bytes del modelo serializado.
        """
        url = f"{self.base_url}/user/{user_id}"
        files = {'model_file': (f'{user_id}_activity_model.pkl', model_bytes, 'application/octet-stream')}

        try:
            print(f"Attempting to upload user {user_id} model to {url}...")
            response = requests.post(url, files=files)
            response.raise_for_status()
            print(f"Successfully uploaded user {user_id} model: {response.json()}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error uploading user {user_id} model to {url}: {e}")
            return False

    def get_user_data_from_cloud(self, user_id: str):
        """
        Obtiene los datos de entrenamiento de un usuario desde la Cloud API.
        Retorna un DataFrame de pandas con los datos.
        """
        url = f"{self.data_url}/user/{user_id}/labeled"
        try:
            print(f"Attempting to fetch labeled data for user {user_id} from {url}...")
            response = requests.get(url) # ¡Sin parámetros de DB!
            response.raise_for_status()
            data = response.json()
            if data and "data" in data:
                df = pd.DataFrame(data["data"])
                if not df.empty:
                    df['timeStamp'] = pd.to_datetime(df['timeStamp'])
                print(f"Successfully fetched {len(df)} labeled data points for user {user_id}.")
                return df
            return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching labeled data for user {user_id} from {url}: {e}")
            return pd.DataFrame()


    def get_user_model_mapping_from_cloud(self, user_id: str):
        """
        Obtiene el mapeo del modelo de un usuario desde la Cloud API.
        Retorna un diccionario con la información del mapeo.
        """
        url = f"{self.users_url}/{user_id}/model_mapping"
        try:
            print(f"Attempting to fetch model mapping for user {user_id} from {url}...")
            response = requests.get(url) # ¡Sin parámetros de DB!
            response.raise_for_status()
            mapping_info = response.json()
            print(f"Successfully fetched model mapping for user {user_id}: {mapping_info}")
            return mapping_info
        except requests.exceptions.RequestException as e:
            print(f"Error fetching model mapping for user {user_id} from {url}: {e}")
            return None

    def update_user_model_mapping_in_cloud(self, user_id: str, model_path: str, model_type: str):
        """
        Actualiza el mapeo del modelo de un usuario en la Cloud API.
        model_path es la ruta del modelo en el sistema de archivos del Fog Node.
        model_type es el tipo de modelo (por ejemplo, "user" o "generic").
        """
        url = f"{self.users_url}/{user_id}/model_mapping" 
        payload = {
            "model_path": model_path,
            "model_type": model_type
        }
        try:
            print(f"Attempting to update model mapping for user {user_id} in {url}...")
            response = requests.put(url, json=payload) # ¡Sin parámetros de DB!
            response.raise_for_status()
            print(f"Successfully updated model mapping for user {user_id}: {response.json()}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error updating model mapping for user {user_id} in {url}: {e}")
            return False