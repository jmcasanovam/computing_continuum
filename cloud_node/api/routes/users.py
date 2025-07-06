# cloud_node/api/routes/users.py
from fastapi import APIRouter, HTTPException
from app.data.database import get_user_model_mapping, update_user_model_mapping

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
    model_path: str,
    model_type: str
):
    """
    Endpoint para actualizar el mapeo del modelo de un usuario.
    """
    try:
        update_user_model_mapping(user_id, model_path, model_type)
        return {"message": f"Model mapping for user {user_id} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating model mapping: {e}")