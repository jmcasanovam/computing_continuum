import threading
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .config import STRATEGY
from .services.node_monitor import monitor_nodes
from .services.node_selector import NodeSelector
from .services.mapek_loop import mapek_loop

app = FastAPI()
selector = NodeSelector(strategy_name=STRATEGY)

@app.get("/api/available-node")
def get_available_node():
    selected_node = selector.select_node()
    if selected_node:
        selected_ip, _ = selected_node
        return JSONResponse(content={"ip": selected_ip})
    return JSONResponse(content={"error": "No hay nodos disponibles"}, status_code=503)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Iniciamos los bucles en hilos separados al lanzar la app
def start_unified_services():
    monitor_thread = threading.Thread(target=monitor_nodes, daemon=True)
    mapek_thread = threading.Thread(target=mapek_loop, daemon=True)

    monitor_thread.start()
    mapek_thread.start()

# Esto se ejecutará al iniciar el Uvicorn
start_unified_services()