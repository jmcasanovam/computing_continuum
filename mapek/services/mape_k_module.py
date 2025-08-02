import time
from typing import Optional, Dict, Any

# --- Almacenamiento de Conocimiento del MAPE-K (simulado en memoria) ---
# En una implementación real, esto se guardaría en una base de datos local o distribuida.
mape_k_knowledge = {
    "sampling_rate_suggestions": {}, # Sugerencias de tasa de muestreo por usuario
    "anomaly_history": {} # Historial de anomalías detectadas
}

# --- Constantes para el Análisis MAPE-K ---
HEART_RATE_THRESHOLD = 100 # Umbral de frecuencia cardíaca para detectar irregularidades
# El umbral de movimiento es un valor de ejemplo y requeriría un análisis más sofisticado
# de los datos de acelerómetro/giróscopo para ser significativo.
MOVEMENT_IRREGULARITY_THRESHOLD = 50 # Umbral de irregularidad de movimiento

# --- Funciones del Bucle MAPE-K (Simplificado) ---
def monitor(processed_data: Dict[str, Any], user_id: str) -> Dict[str, float]:
    """
    Monitoriza los datos procesados y el estado del sistema.
    En una implementación real, aquí se recopilarían métricas de recursos del Edge
    (CPU, memoria, latencia de red, etc.).
    """
    print(f"[{time.time()}] [MAPE-K - Monitor] Monitorizando datos para usuario {user_id}: {processed_data}")
    # Simular métricas de uso de recursos del Edge (valores ficticios por ahora)
    resource_usage = {"cpu_load": 0.5, "memory_usage": 0.3}
    return resource_usage

def analyze(processed_data: Dict[str, Any], resource_usage: Dict[str, float], user_id: str) -> tuple[Optional[str], list[str]]:
    """
    Analiza los datos monitorizados para detectar anomalías o necesidades de adaptación.
    """
    print(f"[{time.time()}] [MAPE-K - Analizar] Analizando datos para usuario {user_id}...")
    anomaly_detected = False
    action_needed = None
    reason = []

    # Ejemplo de análisis: Ritmo cardíaco alto
    if 'heart_rate' in processed_data and processed_data['heart_rate'] > HEART_RATE_THRESHOLD:
        anomaly_detected = True
        action_needed = "adjust_sampling_rate"
        reason.append(f"Ritmo cardíaco alto ({processed_data['heart_rate']} bpm) detectado.")

    # Ejemplo de análisis: Movimiento inusual (basado en pasos)
    # Esta es una comprobación simple. Un análisis real de movimiento requeriría
    # procesar las series de tiempo de acelerómetro y giróscopo.
    if 'steps' in processed_data and processed_data['steps'] > 500:
        print(f"[{time.time()}] Nota: Pasos altos ({processed_data['steps']}), podría indicar actividad intensa.")
        # Esto no se marca como anomalía directa, sino como un punto a considerar.


    if anomaly_detected:
        print(f"[{time.time()}] [MAPE-K - Analizar] Anomalía detectada para usuario {user_id}: {', '.join(reason)}. Acción sugerida: {action_needed}")
        # Guardar en el conocimiento el historial de anomalías
        if user_id not in mape_k_knowledge["anomaly_history"]:
            mape_k_knowledge["anomaly_history"][user_id] = []
        mape_k_knowledge["anomaly_history"][user_id].append({
            "timestamp": int(time.time()),
            "reason": reason,
            "data": processed_data
        })
    else:
        print(f"[{time.time()}] [MAPE-K - Analizar] No se detectaron anomalías significativas para usuario {user_id}.")

    return action_needed, reason

def plan(action_needed: Optional[str], user_id: str) -> Dict[str, Any]:
    """
    Planifica la acción simple a tomar basándose en el análisis.
    """
    print(f"[{time.time()}] [MAPE-K - Planificar] Planificando acción para usuario {user_id}...")
    plan_details = {}
    if action_needed == "adjust_sampling_rate":
        # Simular una decisión: aumentar la tasa de muestreo de la pulsera
        new_sampling_rate = "more_often" # Ejemplo: "más a menudo", "cada 30 segundos"
        plan_details = {"type": "change_sampling_rate", "value": new_sampling_rate}
        print(f"[{time.time()}] [MAPE-K - Planificar] Plan: Cambiar tasa de muestreo a '{new_sampling_rate}' para usuario {user_id}.")
        # Guardar la sugerencia de tasa de muestreo en el conocimiento
        mape_k_knowledge["sampling_rate_suggestions"][user_id] = new_sampling_rate
    else:
        print(f"[{time.time()}] [MAPE-K - Planificar] No hay acción específica planificada.")
    return plan_details

def execute(plan_details: Dict[str, Any], user_id: str) -> str:
    """
    Ejecuta el plan. En este contexto, simula la aplicación del cambio,
    que en una aplicación real implicaría enviar una señal de control.
    """
    print(f"[{time.time()}] [MAPE-K - Ejecutar] Ejecutando plan para usuario {user_id}...")
    execution_status = "success"
    if plan_details and plan_details.get("type") == "change_sampling_rate":
        new_rate = plan_details.get("value")
        print(f"[{time.time()}] [MAPE-K - Ejecutar] Se ha 'solicitado' a la pulsera (simulado) cambiar la tasa de muestreo a: {new_rate} para usuario {user_id}.")
        # En una aplicación real, aquí se enviaría una señal/comando de control
        # de vuelta a la pulsera inteligente o a la aplicación móvil.
    else:
        print(f"[{time.time()}] [MAPE-K - Ejecutar] No hay plan para ejecutar.")
        execution_status = "no_action"
    return execution_status

def self_adapt(processed_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Orquesta el bucle de autoadaptación MAPE-K (Monitor, Analyze, Plan, Execute).
    """
    resource_usage = monitor(processed_data, user_id)
    action_needed, reason = analyze(processed_data, resource_usage, user_id)
    plan_details = plan(action_needed, user_id)
    execution_status = execute(plan_details, user_id)

    # Devolver un resumen de la adaptación realizada y el estado actual sugerido.
    return {
        "mape_k_summary": {
            "action_taken": action_needed,
            "reason": reason,
            "plan_details": plan_details,
            "execution_status": execution_status,
            "current_sampling_suggestion": mape_k_knowledge["sampling_rate_suggestions"].get(user_id, "default")
        }
    }