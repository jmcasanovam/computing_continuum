import time
import requests
from typing import Dict
from ..config import PROMETHEUS_URL

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

        # Asumimos una métrica de Prometheus para el número de usuarios activos
        # Si no existe, podemos simularla o ajustarla más tarde
        active_users_by_ip = query_prometheus('sum by(instance) (users_active_total)')

        # Unimos las métricas por cada IP de nodo
        for ip in set(cpu_usage_by_ip.keys()) | set(memory_usage_by_ip.keys()):
            nodes_status[ip] = {
                "status": "online",
                "current_load": {
                    "cpu_load": cpu_usage_by_ip.get(ip, 0.0),
                    "memory_usage": memory_usage_by_ip.get(ip, 0.0),
                    "active_users_count": active_users_by_ip.get(ip, 0),
                }
            }

        # Marcar nodos que no responden como offline
        online_ips = cpu_usage_by_ip.keys()
        for ip in list(nodes_status.keys()):
            if ip not in online_ips:
                nodes_status[ip]["status"] = "offline"

        time.sleep(5)