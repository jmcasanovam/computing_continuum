# cloud_node/api/main.py
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
# Ya no es necesario cargar dotenv aquí si ya se hace en app.config.py y en el script principal
# from dotenv import load_dotenv

# Importar desde el nuevo archivo de config (asumiendo que 'app' es un paquete ahora)
from app.config import CLOUD_API_PORT #, CLOUD_API_HOST # CLOUD_API_HOST no se usa directamente aquí
from cloud_node.api.routes import models, data, users
import os
import sys


app = FastAPI(
    title="Cloud Model API",
    description="API for managing generic and user-specific machine learning models.",
    version="1.0.0",
)

# Opcional: Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir las rutas de modelos
app.include_router(models.router, prefix="/models", tags=["Models"])
# Incluir las rutas de datos
app.include_router(data.router, prefix="/data", tags=["Data"])
# Incluir las rutas de usuarios
app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/")
async def root():
    return {"message": "Cloud Model API is running!"}

if __name__ == "__main__":
    host_to_bind = "0.0.0.0"
    print(f"Starting Cloud Model API on http://{host_to_bind}:{CLOUD_API_PORT}")
    uvicorn.run(app, host=host_to_bind, port=CLOUD_API_PORT)