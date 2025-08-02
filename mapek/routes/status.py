from fastapi import APIRouter, status, HTTPException
from mapek.services.mape_k_module import monitor, mape_k_knowledge
from typing import Optional, Dict, Any
import time


EDGE_NODE_ID = "node_12345"

last_ingestion_timestamp: Optional[int] = None  # Variable para almacenar el último timestamp de ingesta
active_users: Dict[str, int] = {} # Simular usuarios activos por user_id y timestamp de última actividad

router = APIRouter()
@router.get("/status", status_code=status.HTTP_200_OK)
async def get_status():
    """
    Endpoint para que se supervisen las condiciones de este Nodo.
    Retorna métricas de carga, memoria y estado del sistema.
    """
    current_resource_usage = monitor({}, "manager_query")

    # Limpiar usuarios inactivos (ej. si no han enviado datos en los últimos 5 minutos)
    current_time = int(time.time())
    inactive_threshold = 300 # 5 minutos en segundos
    users_to_remove = [user for user, last_activity in active_users.items() if (current_time - last_activity) > inactive_threshold]
    for user in users_to_remove:
        del active_users[user]

    return {
        "edge_id": EDGE_NODE_ID,
        "status": "online",  # Assume online if responding
        "current_load": {
            "cpu_load": current_resource_usage.get("cpu_load", 0.0),
            "memory_usage": current_resource_usage.get("memory_usage", 0.0),
            "active_users_count": len(active_users),
            "last_ingestion_timestamp": last_ingestion_timestamp,
            "mape_k_knowledge_snapshot": {
                "sampling_rate_suggestions_count": len(mape_k_knowledge["sampling_rate_suggestions"]),
                "anomaly_history_count": sum(len(v) for v in mape_k_knowledge["anomaly_history"].values())
            }
        },
        "message": "Node conditions successfully retrieved."
    }