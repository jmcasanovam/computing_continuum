import time
from typing import Optional, Dict, Any
import requests
from ..config import PROMETHEUS_URL
from app.services.node_monitor import nodes_status # Importamos el estado de los nodos

# --- Almacenamiento de Conocimiento del MAPE-K ---
# En una implementación real, esto se guardaría en una base de datos.
mape_k_knowledge = {
    "sampling_rate_suggestions": {},
    "anomaly_history": {}
}

# --- Funciones MAPE-K (adaptadas) ---
def monitor() -> Dict[str, Dict[str, float]]:
    """
    Monitoriza el estado de los nodos a partir de la información ya obtenida
    por el node_monitor y almacenada en nodes_status.
    """
    return {ip: info["current_load"] for ip, info in nodes_status.items() if info["status"] == "online"}

def analyze(resource_usage: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza el uso de recursos para detectar anomalías.
    """
    print(f"[MAPE-K - Analizar] Analizando el uso de recursos de los nodos...")
    anomalies = {}

    for ip, usage in resource_usage.items():
        # Ejemplo: Si el uso de CPU supera el 50%
        if usage.get("cpu_load", 0.0) > 50:
            anomalies[ip] = {
                "action_needed": "scale_down",
                "reason": f"Uso de CPU alto ({usage['cpu_load']:.2f}%)"
            }
        # Ejemplo: Si la memoria supera el 85%
        if usage.get("memory_usage", 0.0) > 85:
            if ip not in anomalies:
                anomalies[ip] = {"action_needed": "restart_pod"}
            anomalies[ip]["reason"] = f"Uso de memoria alto ({usage['memory_usage']:.2f}%)"

    return anomalies

def plan(anomalies: Dict[str, Any]) -> Dict[str, Any]:
    """
    Planifica la acción a tomar basándose en las anomalías.
    """
    plan_details = {}
    for ip, anomaly in anomalies.items():
        if anomaly.get("action_needed") == "restart_pod":
            plan_details[ip] = {"type": "kubectl_command", "command": f"kubectl rollout restart deployment/edge-service-deployment"}
        elif anomaly.get("action_needed") == "scale_down":
            plan_details[ip] = {"type": "kubectl_command", "command": f"kubectl scale deployment/edge-service-deployment --replicas=0"}
    
    return plan_details

def execute(plan_details: Dict[str, Any]) -> None:
    """
    Ejecuta el plan usando el módulo subprocess para interactuar con kubectl.
    """
    import subprocess
    for ip, plan_data in plan_details.items():
        command = plan_data.get("command")
        if not command:
            print(f"[{time.time()}] [MAPE-K - Ejecutar] No hay comando para el nodo {ip}.")
            continue

        print(f"[{time.time()}] [MAPE-K - Ejecutar] Ejecutando comando para el nodo {ip}: {command}")
        try:
            # Ejecutar el comando de kubectl con el subprocess.run
            # Se usa `check=True` para que lance una excepción si el comando falla
            result = subprocess.run(command.split(), check=True, capture_output=True, text=True)
            print(f"[{time.time()}] Comando ejecutado con éxito para {ip}.")
            print(f"Salida del comando:\n{result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"[{time.time()}] ERROR al ejecutar el comando para {ip}: {e}")
            print(f"Salida de error:\n{e.stderr}")
        except FileNotFoundError:
            print(f"[{time.time()}] ERROR: El comando 'kubectl' no fue encontrado. Asegúrate de que esté instalado y en el PATH del contenedor.")

def mapek_loop():
    """
    Orquesta el bucle de autoadaptación MAPE-K.
    """
    while True:
        print("[MAPE-K] Iniciando ciclo de autoadaptación...")
        
        # 1. Monitorear: Obtener el estado actual
        resource_usage = monitor()
        
        # 2. Analizar: Detectar anomalías
        anomalies = analyze(resource_usage)
        
        if anomalies:
            print("[MAPE-K] Anomalías detectadas:", anomalies)
            # 3. Planificar: Decidir qué hacer
            plan_details = plan(anomalies)
            
            # 4. Ejecutar: Aplicar el plan
            execute(plan_details)
        else:
            print("[MAPE-K] No se detectaron anomalías.")
        
        time.sleep(60) # Ejecutar cada 60 segundos