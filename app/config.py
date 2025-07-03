import os
from dotenv import load_dotenv # <--- ¡NUEVO!

# Cargar variables de entorno desde el archivo .env
# load_dotenv() buscará un archivo .env en el directorio actual o en los padres.
load_dotenv()

# --- Rutas base dentro del contenedor Docker ---
CONTAINER_DATA_DIR = "/app/data"

# --- Configuración de Rutas de Modelos ---
MODELS_DIR = os.path.join(CONTAINER_DATA_DIR, "models")
USER_MODELS_DIR = os.path.join(MODELS_DIR, "users")
GENERIC_MODEL_PATH = os.path.join(MODELS_DIR, "generic_activity_model.pkl")

# --- Configuración de la Base de Datos Central (PostgreSQL) ---
# Se obtienen de las variables de entorno, definidas en .env o pasadas directamente al contenedor
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")

if not all([DB_USER, DB_PASSWORD, DB_NAME, DB_HOST]):
    print("ERROR: Variables de entorno de la base de datos no configuradas. "
          "Asegúrate de que DB_USER, DB_PASSWORD, DB_NAME y DB_HOST estén definidos en .env o en el entorno.", file=os.sys.stderr)
    os.sys.exit(1) # Salir si no están configuradas

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

# --- Configuración de la Cola de Mensajes (Simulada o Real) ---
MESSAGE_QUEUE_DIR = os.path.join(CONTAINER_DATA_DIR, "message_queue")
MESSAGE_QUEUE_FILE = os.path.join(MESSAGE_QUEUE_DIR, "queue.json")

# --- Hosts y Puertos de Servicios ---
# Para servicios dentro de Docker Compose en la misma máquina, se usa el nombre del servicio.
# Para servicios en otras máquinas, necesitarías una variable de entorno para la IP/Hostname real.
# Aquí mantenemos el nombre del servicio como default para uso en el mismo compose.
EDGE_NODE_HOST = os.getenv("EDGE_NODE_HOST", "edge_service") # Puedes definir esto en .env para multi-máquina
EDGE_NODE_PORT = int(os.getenv("EDGE_NODE_PORT", 8000))

# --- Otras Configuraciones ---
FEATURE_COLUMNS = [
    'tic_accx', 'tic_accy', 'tic_accz',
    'tic_acclx', 'tic_accly', 'tic_acclz',
    'tic_girx', 'tic_giry', 'tic_girz',
    'tic_hrppg', 'tic_step'
]

RETRAIN_INTERVAL_HOURS = int(os.getenv("RETRAIN_INTERVAL_HOURS", 1))

MIN_SAMPLES_FOR_FOG_FINE_TUNING = int(os.getenv("MIN_SAMPLES_FOR_FOG_FINE_TUNING", 20))
MIN_GLOBAL_SAMPLES_FOR_CLOUD_RETRAIN = int(os.getenv("MIN_GLOBAL_SAMPLES_FOR_CLOUD_RETRAIN", 500))

# Asegurarse de que los directorios necesarios existan al iniciar el servicio
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(USER_MODELS_DIR, exist_ok=True)
os.makedirs(MESSAGE_QUEUE_DIR, exist_ok=True)