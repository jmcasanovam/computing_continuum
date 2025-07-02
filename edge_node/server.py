from fastapi import FastAPI, HTTPException
from app.schemas.ticwatch_schema import TicWatchData
from app.models.ticwatch_predictor import TicWatchPredictor
from app.data.database import update_user_checkpoint, get_user_model_mapping, insert_ticwatch_data
from app.data.message_queue import publish_message
from app.config import GENERIC_MODEL_PATH, EDGE_NODE_HOST, EDGE_NODE_PORT, FEATURE_COLUMNS
from cloud_node.model_repository import ModelRepository
import os
from datetime import datetime
import asyncio # Para tareas asíncronas en segundo plano

app = FastAPI(title="Edge Node Activity Predictor")

# Diccionario para almacenar los modelos de usuario cargados en memoria
# Esto evita recargar el modelo de disco en cada predicción.
user_predictors: dict[str, TicWatchPredictor] = {}

# Instancia del repositorio de modelos para cargar modelos
model_repo = ModelRepository()

# Variable para identificar este nodo Edge específico (simulada por ahora)
NODE_ID = os.environ.get("EDGE_NODE_ID", "edge_node_1")

async def initialize_edge_node():
    """
    Función de inicialización que se ejecuta al iniciar el servidor FastAPI.
    Podría precargar modelos comunes o realizar verificaciones de DB.
    """
    print(f"Initializing Edge Node: {NODE_ID}")
    # Por ahora, solo asegura que el directorio de modelos exista si no lo hizo antes
    os.makedirs(os.path.dirname(GENERIC_MODEL_PATH), exist_ok=True)
    # También podría precargar el modelo genérico si se sabe que muchos usuarios nuevos lo usarán
    # if os.path.exists(GENERIC_MODEL_PATH):
    #     user_predictors['generic'] = TicWatchPredictor(model_path=GENERIC_MODEL_PATH)
    #     print("Generic model preloaded for Edge Node.")

app.add_event_handler("startup", initialize_edge_node)


@app.post("/predict_activity/{user_id}")
async def predict_activity(user_id: str, data: TicWatchData):
    """
    Recibe datos del TicWatch para un usuario específico, predice la actividad
    y envía los datos para almacenamiento centralizado.
    """
    print(f"Received data for user: {user_id} at timestamp: {data.timeStamp}")

    # --- 1. Cargar o obtener el modelo del usuario ---
    predictor = user_predictors.get(user_id)
    current_model_path = None
    model_type = None

    if predictor is None:
        # El modelo no está en memoria para este usuario, intentar cargarlo
        user_mapping = get_user_model_mapping(user_id)
        if user_mapping:
            current_model_path = user_mapping['model_path']
            model_type = user_mapping['model_type']
            try:
                predictor = TicWatchPredictor(model_path=current_model_path)
                user_predictors[user_id] = predictor
                print(f"Loaded custom model for user {user_id} from {current_model_path}")
            except FileNotFoundError:
                print(f"Custom model for user {user_id} not found at {current_model_path}. Falling back to generic.")
                current_model_path = GENERIC_MODEL_PATH
                model_type = "generic"
                predictor = TicWatchPredictor(model_path=current_model_path)
                user_predictors[user_id] = predictor
            except Exception as e:
                print(f"Error loading custom model for user {user_id}: {e}. Falling back to generic.")
                current_model_path = GENERIC_MODEL_PATH
                model_type = "generic"
                predictor = TicWatchPredictor(model_path=current_model_path)
                user_predictors[user_id] = predictor
        else:
            # Usuario nuevo o sin mapeo, usar modelo genérico
            current_model_path = GENERIC_MODEL_PATH
            model_type = "generic"
            try:
                predictor = TicWatchPredictor(model_path=current_model_path)
                user_predictors[user_id] = predictor
                print(f"Loaded generic model for new user {user_id}.")
            except FileNotFoundError:
                raise HTTPException(status_code=500, detail=f"Generic model not found at {GENERIC_MODEL_PATH}. Cannot process data.")
    
    if predictor.model is None:
        raise HTTPException(status_code=500, detail="Model could not be loaded for prediction.")

    # --- 2. Realizar la predicción ---
    try:
        predicted_state = predictor.predict(data)
        print(f"Prediction for user {user_id} at {data.timeStamp}: {predicted_state}")
    except Exception as e:
        print(f"Error during prediction for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    # --- 3. Enviar datos a la cola de mensajes (para almacenamiento y re-entrenamiento) ---
    # Convertir TicWatchData a un diccionario, añadir user_id y predicted_state
    data_to_queue = data.model_dump()
    data_to_queue['user_id'] = user_id
    data_to_queue['predicted_state'] = predicted_state
    
    # Esta es una simulación asíncrona de publicación.
    # En un entorno real, usarías un cliente de Kafka/RabbitMQ no bloqueante.
    # Usamos asyncio.create_task para que no bloquee la respuesta HTTP.
    asyncio.create_task(publish_message_async(data_to_queue))
    
    # --- 4. Actualizar el checkpoint del usuario (asíncronamente) ---
    # El checkpoint registra el último timestamp procesado y la versión del modelo usada
    asyncio.create_task(update_checkpoint_async(user_id, data.timeStamp, current_model_path, NODE_ID))

    return {"user_id": user_id, "predicted_activity": predicted_state, "timestamp": data.timeStamp}

async def publish_message_async(message: dict):
    """Función asíncrona para publicar un mensaje en la cola."""
    # Simula un ligero retardo de red o procesamiento para la tarea en segundo plano
    # await asyncio.sleep(0.01) 
    publish_message(message)
    # print(f"Background task: Message published for user {message.get('user_id')}")

async def update_checkpoint_async(user_id: str, timestamp: datetime, model_version: str, node_id: str):
    """Función asíncrona para actualizar el checkpoint del usuario."""
    # await asyncio.sleep(0.01)
    update_user_checkpoint(user_id, timestamp, model_version, node_id)
    # print(f"Background task: Checkpoint updated for user {user_id}")

# Para ejecutar el servidor con Uvicorn (usado en Dockerfile)
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host=EDGE_NODE_HOST, port=EDGE_NODE_PORT)