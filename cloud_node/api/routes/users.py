# cloud_node/api/routes/users.py
from fastapi import APIRouter, HTTPException, Body
from app.data.database import get_user_model_mapping, update_user_model_mapping
from app.schemas.user_schemas import ModelMappingUpdate
from app.config import GENERIC_MODEL_PATH

router = APIRouter()

@router.get("/{user_id}/model_mapping")
async def get_model_mapping(user_id: str):
    """
    Endpoint para obtener el mapeo del modelo de un usuario.
    """
    try:
        mapping = get_user_model_mapping(user_id)
        if mapping:
            return mapping
        else:
            raise HTTPException(status_code=404, detail=f"Model mapping for user {user_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching model mapping: {e}")

@router.put("/{user_id}/model_mapping")
async def update_model_mapping(
    user_id: str,
    # CORRECCIÓN CLAVE: Usar un modelo Pydantic para el cuerpo de la petición
    # FastAPI parseará automáticamente el JSON del cuerpo en este objeto.
    update_data: ModelMappingUpdate = Body(...) # <-- CAMBIO AQUÍ
):
    """
    Endpoint para actualizar el mapeo del modelo de un usuario.
    """
    try:
        # Acceder a los datos desde update_data
        update_user_model_mapping(user_id, update_data.model_path, update_data.model_type)
        return {"message": f"Model mapping for user {user_id} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating model mapping: {e}")

@router.post("/{user_id}/set_generic_model")
async def set_generic_model(user_id: str):
    """
    Endpoint para establecer el modelo del usuario como el modelo genérico.
    """
    try:
        # Asumimos que el modelo genérico tiene valores predefinidos
        generic_model_path = GENERIC_MODEL_PATH
        generic_model_type = "generic"
        update_user_model_mapping(user_id, generic_model_path, generic_model_type)
        return {"message": f"Model mapping for user {user_id} set to generic model successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting generic model: {e}")