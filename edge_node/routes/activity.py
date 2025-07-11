from fastapi import APIRouter, HTTPException
from app.schemas.ticwatch_schema import TicWatchData
from app.models.ticwatch_predictor import TicWatchPredictor
from app.data.database import get_user_model_mapping
from datetime import datetime
import asyncio
import sys
# Importar variables y funciones globales desde server.py
from edge_node.server import user_predictors, cloud_api_client, publish_data_message_async

router = APIRouter()

@router.post("/{user_id}") # La ruta base es /predict_activity, definida en server.py
async def predict_activity(user_id: str, data: TicWatchData):
    """
    Recibe datos del TicWatch para un usuario específico, predice la actividad
    y envía los datos para almacenamiento centralizado.
    """
    print(f"Received data for user: {user_id} at timestamp: {data.timestamp}", file=sys.stderr)

    # --- 1. Cargar o obtener el modelo del usuario ---
    predictor = user_predictors.get(user_id)
    model_type = None

    if predictor is None:
        user_mapping = get_user_model_mapping(user_id)
        
        model_bytes = None
        if user_mapping and user_mapping['model_path']:
            model_type = user_mapping['model_type']
            try:
                if model_type == "personalized":
                    print(f"Loading personalized model for user {user_id} from Cloud API...", file=sys.stderr)
                    model_bytes = cloud_api_client.download_model(user_id=user_id)
                else:
                    print(f"Unknown or generic model_type: {model_type} for user {user_id}. Falling back to generic.", file=sys.stderr)
                    model_bytes = cloud_api_client.download_model(user_id=None)
                    model_type = "generic"

                if model_bytes:
                    predictor = TicWatchPredictor(model_bytes=model_bytes)
                    user_predictors[user_id] = predictor
                    print(f"Loaded {model_type} model for user {user_id} from Cloud API.", file=sys.stderr)
                else:
                    raise HTTPException(status_code=500, detail=f"{model_type.capitalize()} model not found. Cannot process data for user {user_id}.")
            except Exception as e:
                print(f"Error loading custom model for user {user_id}: {e}. Falling back to generic.", file=sys.stderr)
                model_bytes = cloud_api_client.download_model(user_id=None)
                model_type = "generic"
                if model_bytes:
                    predictor = TicWatchPredictor(model_bytes=model_bytes)
                    user_predictors[user_id] = predictor
                    print(f"Loaded generic model after custom model fallback for user {user_id}.", file=sys.stderr)
                else:
                    raise HTTPException(status_code=500, detail=f"Generic model not found. Cannot process data for user {user_id}.")
        else:
            print(f"New user {user_id} or no mapping found. Downloading generic model.", file=sys.stderr)
            model_bytes = cloud_api_client.download_model(user_id=None)
            model_type = "generic"
            if model_bytes:
                predictor = TicWatchPredictor(model_bytes=model_bytes)
                user_predictors[user_id] = predictor
                print(f"Loaded generic model for new user {user_id}.", file=sys.stderr)
            else:
                raise HTTPException(status_code=500, detail=f"Generic model not found. Cannot process data for user {user_id}.")
    
    if predictor is None or predictor.model is None:
        raise HTTPException(status_code=500, detail="Model could not be loaded for prediction.")

    # --- 2. Realizar la predicción ---
    try:
        predicted_state = predictor.predict(data)
        print(f"Prediction for user {user_id} at {data.timestamp}: {predicted_state}", file=sys.stderr)
    except Exception as e:
        print(f"Error during prediction for user {user_id}: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    # --- 3. Enviar datos a la cola de mensajes (para almacenamiento y re-entrenamiento) ---
    data_to_queue = data.model_dump()
    data_to_queue['user_id'] = user_id
    data_to_queue['predicted_state'] = predicted_state
    data_to_queue['timestamp'] = data.timestamp.isoformat()
    
    asyncio.create_task(publish_data_message_async(data_to_queue))

    return {"user_id": user_id, "predicted_activity": predicted_state, "timestamp": data.timestamp}