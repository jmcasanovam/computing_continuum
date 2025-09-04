# app/main.py

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .config import STRATEGY
from .services.node_monitor import monitor_nodes
from .services.node_selector import NodeSelector
from .services.mapek_loop import mapek_loop
from .shared_state import user_count_lock, active_users_per_node
import threading

app = FastAPI()
selector = NodeSelector(strategy_name=STRATEGY)

print("🚀 Inicio manager-mapek")

@app.on_event("startup")
def startup_event():
    """Se ejecuta al iniciar el servidor para lanzar los hilos."""
    monitor_thread = threading.Thread(target=monitor_nodes, daemon=True)
    mapek_thread = threading.Thread(target=mapek_loop, daemon=True)

    monitor_thread.start()
    mapek_thread.start()

@app.get("/api/available-node")
def get_available_node():
    selected_node_info = selector.select_node()
    if selected_node_info:
        selected_ip, _ = selected_node_info
        with user_count_lock:
            active_users_per_node[selected_ip] = active_users_per_node.get(selected_ip, 0) + 1
        print(f"Node selected: {selected_ip}, Active users: {active_users_per_node[selected_ip]}")
        return JSONResponse(content={"ip": selected_ip})
    return JSONResponse(content={"error": "No hay nodos disponibles"}, status_code=503)

@app.get("/health")
def health_check():
    return {"status": "ok"}