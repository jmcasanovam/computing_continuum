from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.services.node_selector import NodeSelector
from app.config import STRATEGY
from app.services.node_monitor import start_monitoring

app = FastAPI()

selector = NodeSelector(strategy_name=STRATEGY)

@app.get("/api/available-node")
def get_available_node():
    selected_ip = selector.select_node()
    if selected_ip:
        return JSONResponse(content={"ip": selected_ip})
    return JSONResponse(content={"error": "No hay nodos disponibles"}, status_code=503)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Iniciamos la monitorización al lanzar la app
start_monitoring()
