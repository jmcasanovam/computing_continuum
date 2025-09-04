from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.services.node_selector import NodeSelector
from app.config import STRATEGY
from app.services.node_monitor import start_monitoring
import threading

# Un lock para asegurar la seguridad de los hilos al modificar el contador
user_count_lock = threading.Lock()
# Diccionario para almacenar el conteo de usuarios por IP de nodo
active_users_per_node = {}

app = FastAPI()

selector = NodeSelector(strategy_name=STRATEGY)

print("Inicio manager-mapek")

@app.get("/api/available-node")
def get_available_node():
    selected_ip = selector.select_node()
    if selected_ip:
        with user_count_lock:
            if selected_ip not in active_users_per_node:
                active_users_per_node[selected_ip] = 0
            active_users_per_node[selected_ip] += 1
        print(f"Node selected: {selected_ip}, Active users: {active_users_per_node[selected_ip]}")
        return JSONResponse(content={"ip": selected_ip})
    return JSONResponse(content={"error": "No hay nodos disponibles"}, status_code=503)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Iniciamos la monitorización al lanzar la app
start_monitoring()
