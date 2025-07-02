import os

# Rutas dentro del contenedor Docker.
# Estas rutas se mapearán a volúmenes persistentes en el host.
CONTAINER_DATA_DIR = "/app/data" # Directorio de datos dentro del contenedor

# --- Configuración de Rutas de Modelos ---
MODEL_BASE_DIR = os.path.join(CONTAINER_DATA_DIR, "models")
GENERIC_MODEL_PATH = os.path.join(MODEL_BASE_DIR, "generic_activity_model.pkl")

# --- Configuración de la Base de Datos Central ---
# La DB SQLite estará dentro del volumen "database"
DATABASE_URL = os.path.join(CONTAINER_DATA_DIR, "database", "app_database.db")

# --- Configuración de la Cola de Mensajes (Simulada) ---
MESSAGE_QUEUE_FILE = os.path.join(CONTAINER_DATA_DIR, "message_queue", "queue.json")

# --- Hosts y Puertos de Servicios ---
# Usaremos nombres de servicio de Docker Compose para la comunicación interna
# En una red Docker, 'edge_service' resolverá a la IP del contenedor Edge.
EDGE_NODE_HOST = "edge_service" # Nombre del servicio en docker-compose
EDGE_NODE_PORT = 8000

# --- Otros ---
FEATURE_COLUMNS = [
    'tic_accx', 'tic_accy', 'tic_accz',
    'tic_acclx', 'tic_accly', 'tic_acclz',
    'tic_girx', 'tic_giry', 'tic_girz',
    'tic_hrppg', 'tic_step'
]