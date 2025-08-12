import time
import requests
from typing import Dict
from ..config import PROMETHEUS_URL
from ..shared_state import active_users_per_node, user_count_lock

# Diccionario para almacenar el estado de los nodos
nodes_status: Dict[str, Dict] = {}

def query_prometheus(metric: str) -> Dict[str, float]:
    """Consulta Prometheus y devuelve las métricas por instancia (IP del nodo)."""
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": metric},
            timeout=5
        )
        response.raise_for_status()
        result = response.json()

        data = {}
        for item in result['data']['result']:
            instance_ip = item['metric']['instance'].split(':')[0]
            value = float(item['value'][1])
            data[instance_ip] = value
        return data
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        print(f"Error al consultar Prometheus para la métrica {metric}: {e}")
        return {}

def monitor_nodes():
    """Monitorea el estado de los nodos consultando Prometheus."""
    while True:
        # Consulta el uso de CPU y memoria
        cpu_usage_by_ip = query_prometheus('100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)')
        memory_usage_by_ip = query_prometheus('(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100')

        # El primer bucle es para actualizar los nodos que están online
        for ip in set(cpu_usage_by_ip.keys()) | set(memory_usage_by_ip.keys()):
            # Si el nodo no existe, se inicializa
            if ip not in nodes_status:
                nodes_status[ip] = {
                    "status": "online",
                    "current_load": {
                        "cpu_load": 0.0,
                        "memory_usage": 0.0,
                        "active_users_count": 0
                    }
                }
            
            nodes_status[ip]["status"] = "online"
            nodes_status[ip]["current_load"]["cpu_load"] = cpu_usage_by_ip.get(ip, 0.0)
            nodes_status[ip]["current_load"]["memory_usage"] = memory_usage_by_ip.get(ip, 0.0)
        
        # Marcar nodos que no responden como offline y reiniciar su contador de usuarios
        online_ips = cpu_usage_by_ip.keys()
        with user_count_lock:
            for ip in list(nodes_status.keys()):
                if ip not in online_ips:
                    nodes_status[ip]["status"] = "offline"
                    # Reiniciamos el contador del nodo offline
                    active_users_per_node[ip] = 0
                else:
                    # Sincronizamos el contador de usuarios para los nodos online
                    nodes_status[ip]["current_load"]["active_users_count"] = active_users_per_node.get(ip, 0)

        time.sleep(5)