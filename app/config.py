# your_project_root/app/config.py

import os

# Rutas base dentro del contenedor Docker.
# Estas rutas se mapearán a volúmenes persistentes en el host.
CONTAINER_DATA_DIR = "/app/data" # Directorio de datos persistentes dentro del contenedor

# --- Configuración de Rutas de Modelos ---
# Directorio base para todos los modelos (genéricos y personalizados)
MODELS_DIR = os.path.join(CONTAINER_DATA_DIR, "models") # <--- ¡AÑADIDO/CORREGIDO!

# Directorio para modelos personalizados de usuarios
USER_MODELS_DIR = os.path.join(MODELS_DIR, "users") # <--- ¡AÑADIDO!

# Ruta completa para el archivo del modelo genérico
GENERIC_MODEL_PATH = os.path.join(MODELS_DIR, "generic_activity_model.pkl") # <--- CORREGIDO para usar MODELS_DIR

# --- Configuración de la Base de Datos Central (SQLite en este caso) ---
DATABASE_DIR = os.path.join(CONTAINER_DATA_DIR, "database") # <--- AÑADIDO para consistencia
DATABASE_URL = os.path.join(DATABASE_DIR, "app_database.db") # <--- CORREGIDO para usar DATABASE_DIR

# --- Configuración de la Cola de Mensajes (Simulada) ---
MESSAGE_QUEUE_DIR = os.path.join(CONTAINER_DATA_DIR, "message_queue") # <--- AÑADIDO para consistencia
MESSAGE_QUEUE_FILE = os.path.join(MESSAGE_QUEUE_DIR, "queue.json") # <--- CORREGIDO para usar MESSAGE_QUEUE_DIR

# --- Hosts y Puertos de Servicios ---
# Usaremos nombres de servicio de Docker Compose para la comunicación interna
# En una red Docker, 'edge_service' resolverá a la IP del contenedor Edge.
EDGE_NODE_HOST = "edge_service" # Nombre del servicio en docker-compose
EDGE_NODE_PORT = 8000

# --- Otras Configuraciones ---
# Columnas de características que espera el modelo
FEATURE_COLUMNS = [
    'tic_accx', 'tic_accy', 'tic_accz',
    'tic_acclx', 'tic_accly', 'tic_acclz',
    'tic_girx', 'tic_giry', 'tic_girz',
    'tic_hrppg', 'tic_step'
]

# Umbrales para el entrenamiento (ejemplos, se pueden ajustar)
MIN_SAMPLES_FOR_FOG_FINE_TUNING = 20 # Mínimo de muestras etiquetadas para fine-tuning en Fog
MIN_GLOBAL_SAMPLES_FOR_CLOUD_RETRAIN = 500 # Mínimo de muestras globales para re-entrenamiento en Cloud