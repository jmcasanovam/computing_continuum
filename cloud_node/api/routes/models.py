import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from cloud_node.api.dependencies import get_model_repository
from cloud_node.model_repository import ModelRepository # Tipo para la dependencia

router = APIRouter()

# Endpoint para descargar el modelo genérico
@router.get("/generic")
async def get_generic_model(model_repository: ModelRepository = Depends(get_model_repository)):
    model_path = model_repository.get_generic_model_path()
    if os.path.exists(model_path):
        # Media type es importante para que el cliente sepa qué tipo de archivo recibe
        return FileResponse(path=model_path, media_type='application/octet-stream', filename='generic_activity_model.pkl')
    else:
        raise HTTPException(status_code=404, detail="Generic model not found")

# Endpoint para subir un modelo de usuario
@router.post("/user/{user_id}")
async def upload_user_model(user_id: str, model_file: UploadFile = File(...), model_repository: ModelRepository = Depends(get_model_repository)):
    # Generar la ruta para guardar el modelo de usuario
    save_path = model_repository.get_user_model_path(user_id)

    try:
        # Escribir el archivo recibido
        with open(save_path, "wb") as buffer:
            # chunk_size para manejar archivos grandes eficientemente
            while contents := await model_file.read(1024 * 1024): # Lee en bloques de 1MB
                buffer.write(contents)

        return {"message": f"User model for {user_id} uploaded successfully", "path": save_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save user model: {str(e)}")

# Endpoint para descargar un modelo de usuario
@router.get("/user/{user_id}")
async def get_user_model(user_id: str, model_repository: ModelRepository = Depends(get_model_repository)):
    model_path = model_repository.get_user_model_path(user_id)
    if os.path.exists(model_path):
        return FileResponse(path=model_path, media_type='application/octet-stream', filename=f'{user_id}_activity_model.pkl')
    else:
        raise HTTPException(status_code=404, detail=f"User model for {user_id} not found")