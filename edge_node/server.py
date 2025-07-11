from fastapi import FastAPI
from app.data.message_queue import publish_data_message
from fog_node.cloud_api_client import CloudAPIClient
import os
from datetime import datetime
import asyncio
import sys

# --- Variables Globales y Clientes Compartidos ---
# Instancia de FastAPI
app = FastAPI(title="Edge Node Activity Predictor")

# Diccionario para almacenar los modelos de usuario cargados en memoria
user_predictors: dict[str, any] = {}

# Instancia del cliente de la Cloud API para descargar modelos
cloud_api_client = CloudAPIClient()

# Variable para identificar este nodo Edge específico
NODE_ID = os.environ.get("EDGE_NODE_ID", "edge_node")

# --- Funciones Asíncronas de Segundo Plano ---
async def publish_data_message_async(message: dict):
    """Función asíncrona para publicar un mensaje en la cola."""
    try:
        # Publicar el mensaje de datos en la cola de ingesta
        publish_data_message(message)
        print(f"Background task: Message published for user {message.get('user_id')}", file=sys.stderr)
    except Exception as e:
        print(f"Background task: Error publishing message for user {message.get('user_id')}: {e}", file=sys.stderr)


# --- Inicialización del Nodo Edge ---
async def initialize_edge_node():
    """
    Función de inicialización que se ejecuta al iniciar el servidor FastAPI.
    """
    print(f"Initializing Edge Node: {NODE_ID}", file=sys.stderr)
    # Opcional: Precargar el modelo genérico al inicio del Edge para reducir latencia en nuevos usuarios
    try:
        generic_model_bytes = cloud_api_client.download_model(user_id=None)
        if generic_model_bytes:
            # TicWatchPredictor se importa aquí para evitar dependencia circular al inicio
            from app.models.ticwatch_predictor import TicWatchPredictor
            user_predictors['generic_fallback'] = TicWatchPredictor(model_bytes=generic_model_bytes)
            print("Generic model preloaded for Edge Node.", file=sys.stderr)
        else:
            print("Warning: Could not preload generic model for Edge Node.", file=sys.stderr)
    except Exception as e:
        print(f"Error preloading generic model: {e}", file=sys.stderr)

app.add_event_handler("startup", initialize_edge_node)

# --- Registro de Rutas ---
# Importar el router de rutas
from edge_node.routes.activity import router as activity_router

# Incluir el router en la aplicación principal de FastAPI
app.include_router(activity_router, prefix="/predict_activity", tags=["Activity Prediction"])

