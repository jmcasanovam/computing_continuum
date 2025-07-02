import sqlite3
import pandas as pd
from app.config import DATABASE_URL, FEATURE_COLUMNS
from datetime import datetime
import os

# Asegurarse de que el directorio de la base de datos exista
db_dir = os.path.dirname(DATABASE_URL)
os.makedirs(db_dir, exist_ok=True)


# Conexión global para simplificar el ejemplo.
# En una aplicación real, usarías un pool de conexiones o inyección de dependencias.
conn = None

def get_db_connection():
    global conn
    if conn is None:
        try:
            conn = sqlite3.connect(DATABASE_URL, detect_types=sqlite3.PARSE_DECLTYPES)
            conn.row_factory = sqlite3.Row # Para acceder a columnas por nombre
        except sqlite3.Error as e:
            print(f"Error al conectar con la base de datos en {DATABASE_URL}: {e}")
            conn = None # Asegurarse de que la conexión es nula si falla
    return conn

def create_tables():
    """Crea las tablas necesarias en la base de datos."""
    conn = get_db_connection()
    if conn is None:
        print("No se pudo obtener conexión a la base de datos para crear tablas.")
        return

    cursor = conn.cursor()

    # Tabla para almacenar los datos del TicWatch para el entrenamiento
    # Incluye las características, user_id, timestamp, predicción y estado_real (etiqueta de verdad)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS ticwatch_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            tic_accx REAL,
            tic_accy REAL,
            tic_accz REAL,
            tic_acclx REAL,
            tic_accly REAL,
            tic_acclz REAL,
            tic_girx REAL,
            tic_giry REAL,
            tic_girz REAL,
            tic_hrppg REAL,
            tic_step INTEGER,
            predicted_state TEXT,
            estado_real TEXT, -- Esta es la columna clave para el entrenamiento
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Tabla para almacenar los checkpoints de los usuarios en los nodos Edge
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_checkpoints (
            user_id TEXT PRIMARY KEY,
            last_processed_timestamp TIMESTAMP,
            current_model_version TEXT, -- La versión del modelo que el Edge está usando para este usuario
            node_id TEXT, -- Qué nodo Edge estaba procesando este usuario (para depuración/monitoreo)
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Tabla para mapear user_id a su modelo personalizado activo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_model_mapping (
            user_id TEXT PRIMARY KEY,
            model_path TEXT NOT NULL, -- Ruta al archivo del modelo personalizado o genérico
            model_type TEXT NOT NULL, -- 'generic' o 'personalizado'
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    print("Tablas de la base de datos creadas/verificadas.")

def insert_ticwatch_data(data: dict):
    """Inserta un registro de datos del TicWatch en la tabla ticwatch_data."""
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    
    # Preparar los datos para la inserción
    columns = ["session_id", "user_id", "timestamp"] + FEATURE_COLUMNS + ["predicted_state", "estado_real"]
    values_placeholder = ', '.join(['?'] * len(columns))
    
    # Asegurarse de que todas las columnas de características están presentes en el dict de datos
    feature_values = [data.get(col) for col in FEATURE_COLUMNS]
    
    # Formatear la fecha/hora para SQLite
    timestamp_str = data['timeStamp'].isoformat() if isinstance(data['timeStamp'], datetime) else data['timeStamp']

    values = (
        data['session_id'],
        data.get('user_id', 'unknown_user'), # Asumir un user_id si no viene
        timestamp_str,
        *feature_values, # Desempaquetar los valores de las características
        data.get('predicted_state'),
        data.get('estado_real')
    )
    
    try:
        cursor.execute(f"INSERT INTO ticwatch_data ({', '.join(columns)}) VALUES ({values_placeholder})", values)
        conn.commit()
        # print(f"Datos de sesión {data['session_id']} guardados en DB.")
    except sqlite3.Error as e:
        print(f"Error al insertar datos en la base de datos: {e}")

def get_user_data(user_id: str, limit: int = None) -> pd.DataFrame:
    """Recupera datos de un usuario específico de la base de datos."""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    
    query = f"SELECT {', '.join(['timestamp'] + FEATURE_COLUMNS + ['estado_real'])} FROM ticwatch_data WHERE user_id = ?"
    if limit:
        query += f" ORDER BY timestamp DESC LIMIT {limit}" # Ordena para obtener los más recientes si hay límite
    
    try:
        df = pd.read_sql_query(query, conn, params=(user_id,), parse_dates=['timestamp'])
        return df
    except Exception as e:
        print(f"Error al obtener datos del usuario {user_id}: {e}")
        return pd.DataFrame()

def get_all_training_data() -> pd.DataFrame:
    """Recupera todos los datos con 'estado_real' no nulo de la base de datos."""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()

    query = f"SELECT {', '.join(['timestamp'] + FEATURE_COLUMNS + ['estado_real'])} FROM ticwatch_data WHERE estado_real IS NOT NULL"
    
    try:
        df = pd.read_sql_query(query, conn, parse_dates=['timestamp'])
        return df
    except Exception as e:
        print(f"Error al obtener todos los datos de entrenamiento: {e}")
        return pd.DataFrame()

def update_user_checkpoint(user_id: str, timestamp: datetime, model_version: str, node_id: str):
    """Actualiza el checkpoint de un usuario."""
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO user_checkpoints (user_id, last_processed_timestamp, current_model_version, node_id)
            VALUES (?, ?, ?, ?);
        """, (user_id, timestamp.isoformat(), model_version, node_id))
        conn.commit()
        # print(f"Checkpoint para usuario {user_id} actualizado.")
    except sqlite3.Error as e:
        print(f"Error al actualizar checkpoint: {e}")

def get_user_checkpoint(user_id: str) -> dict | None:
    """Recupera el último checkpoint de un usuario."""
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT last_processed_timestamp, current_model_version, node_id FROM user_checkpoints WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            # Convertir timestamp de nuevo a datetime si es necesario
            timestamp = datetime.fromisoformat(row['last_processed_timestamp']) if row['last_processed_timestamp'] else None
            return {
                "last_processed_timestamp": timestamp,
                "current_model_version": row['current_model_version'],
                "node_id": row['node_id']
            }
        return None
    except sqlite3.Error as e:
        print(f"Error al obtener checkpoint: {e}")
        return None

def update_user_model_mapping(user_id: str, model_path: str, model_type: str):
    """Actualiza el mapeo de usuario a modelo activo."""
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO user_model_mapping (user_id, model_path, model_type)
            VALUES (?, ?, ?);
        """, (user_id, model_path, model_type))
        conn.commit()
        print(f"Mapeo de modelo para usuario {user_id} actualizado a {model_path} ({model_type}).")
    except sqlite3.Error as e:
        print(f"Error al actualizar mapeo de modelo: {e}")

def get_user_model_mapping(user_id: str) -> dict | None:
    """Recupera el mapeo de modelo para un usuario."""
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT model_path, model_type FROM user_model_mapping WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                "model_path": row['model_path'],
                "model_type": row['model_type']
            }
        return None
    except sqlite3.Error as e:
        print(f"Error al obtener mapeo de modelo: {e}")
        return None


if __name__ == "__main__":
    # Asegurarse de que el directorio de la base de datos exista antes de conectar
    db_dir = os.path.dirname(DATABASE_URL)
    os.makedirs(db_dir, exist_ok=True)
    
    print("Inicializando base de datos...")
    create_tables()
    print("Base de datos lista.")