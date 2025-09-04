from fastapi import FastAPI
from mapek.routes.status import router as status_router


# --- Variables Globales y Clientes Compartidos ---
# Instancia de FastAPI
app = FastAPI(title="Edge Node Activity Predictor")



@app.get("/health")
def health_check():
    return {"status": "ok"}

# --- Registro de Rutas ---
app.include_router(status_router, tags=["Status"])
