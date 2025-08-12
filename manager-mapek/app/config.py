import os

# --- Configuración del Servicio Unificado ---
STRATEGY = os.getenv("STRATEGY", "weighted") # Estrategia por defecto
# La URL de Prometheus para la monitorización
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus.monitoring.svc.cluster.local:9090")