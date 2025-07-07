from fastapi import APIRouter, HTTPException
import pandas as pd
from app.data.database import get_user_data, insert_ticwatch_data
import sys
import traceback

router = APIRouter()

@router.get("/user/{user_id}/labeled")
async def get_labeled_user_data(user_id: str):
    """
    Endpoint para que el Fog Trainer obtenga los datos etiquetados de un usuario.
    """
    print(f"Obteniendo datos de usuario {user_id} desde PostgreSQL...", file=sys.stderr)
    try:
        df = get_user_data(user_id)
        if df.empty:
            print(f"No se encontraron datos etiquetados para el usuario {user_id}.", file=sys.stderr)
            return {"data": []}
        
        # CORRECCIÓN CLAVE: Convertir columnas de tipo datetime a string usando .astype(str)
        # Esto es más robusto y maneja la serialización a JSON automáticamente.
        for col in ['timestamp', 'created_at']:
            if col in df.columns and pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].astype(str) # Convertir a string
        
        print(f"Datos etiquetados recuperados para el usuario {user_id}: {len(df)} filas.", file=sys.stderr)
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        print(f"ERROR en get_labeled_user_data para user {user_id}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Error fetching labeled data: {e}")