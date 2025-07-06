from fastapi import APIRouter, HTTPException
import pandas as pd
from app.data.database import get_user_data

router = APIRouter()

@router.get("/user/{user_id}/labeled")
async def get_labeled_user_data(user_id: str):
    """
    Endpoint para que el Fog Trainer obtenga los datos etiquetados de un usuario.
    """
    try:
        df = get_user_data(user_id)
        if df.empty:
            return {"data": []}
        # Asegurarse de que el timestamp sea un formato serializable a JSON
        df['timeStamp'] = df['timeStamp'].astype(str)
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching labeled data: {e}")
