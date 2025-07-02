# your_project_root/app/data/database.py

import sqlite3
import pandas as pd
from app.config import DATABASE_URL, FEATURE_COLUMNS
from datetime import datetime
import os
from typing import Optional
import sys # Importar sys para stderr
import pdb

# Asegurarse de que el directorio de la base de datos exista
db_dir = os.path.dirname(DATABASE_URL)
os.makedirs(db_dir, exist_ok=True)

# Conexión global. Por defecto, NO configuramos row_factory aquí.
conn = None

def get_db_connection():
    """
    Obtiene una conexión de DB. Esta conexión no tiene row_factory activado por defecto.
    """
    global conn
    if conn is None:
        try:
            conn = sqlite3.connect(DATABASE_URL, detect_types=sqlite3.PARSE_DECLTYPES)
            # No establecer conn.row_factory = sqlite3.Row aquí.
        except sqlite3.Error as e:
            print(f"Error al conectar con la base de datos en {DATABASE_URL}: {e}", file=sys.stderr)
            conn = None
    return conn

# Eliminamos get_plain_db_connection()

def create_tables():
    """Crea las tablas necesarias en la base de datos."""
    conn = get_db_connection()
    if conn is None:
        print("No se pudo obtener conexión a la base de datos para crear tablas.", file=sys.stderr)
        return

    cursor = conn.cursor()
    # ... (el resto de tu código de create_tables es el mismo) ...
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_checkpoints (
            user_id TEXT PRIMARY KEY,
            last_processed_timestamp TIMESTAMP,
            current_model_version TEXT,
            node_id TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_model_mapping (
            user_id TEXT PRIMARY KEY,
            model_path TEXT NOT NULL,
            model_type TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    print("Tablas de la base de datos creadas/verificadas.", file=sys.stderr)

def insert_ticwatch_data(data: dict):
    """Inserta un registro de datos del TicWatch en la tabla ticwatch_data."""
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()

    columns = ["session_id", "user_id", "timestamp"] + FEATURE_COLUMNS + ["predicted_state", "estado_real"]
    values_placeholder = ', '.join(['?'] * len(columns))

    feature_values = [data.get(col) for col in FEATURE_COLUMNS]

    # --- CAMBIO CLAVE AQUÍ: Asumir que 'timeStamp' ya es una cadena formateada ---
    timestamp_to_insert = data['timeStamp'] 

    values = (
        data['session_id'],
        data.get('user_id', 'unknown_user'),
        timestamp_to_insert, # Usar directamente el string formateado
        *feature_values,
        data.get('predicted_state'),
        data.get('estado_real')
    )

    try:
        cursor.execute(f"INSERT INTO ticwatch_data ({', '.join(columns)}) VALUES ({values_placeholder})", values)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al insertar datos en la base de datos: {e}", file=sys.stderr)

def get_user_data(user_id: str, limit: Optional[int] = None) -> pd.DataFrame:
    """Recupera datos de un usuario específico de la base de datos."""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    
    # --- CAMBIO CLAVE AQUÍ: Asegurarse de que row_factory sea None para esta operación ---
    original_row_factory = conn.row_factory
    conn.row_factory = None # Forzar a None para pandas
    
    query = f"SELECT {', '.join(['timestamp'] + FEATURE_COLUMNS + ['estado_real'])} FROM ticwatch_data WHERE user_id = ?"
    if limit:
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
    
    try:
        df = pd.read_sql_query(query, conn, params=(user_id,), parse_dates=['timestamp'])
        return df
    except Exception as e:
        print(f"Error al obtener datos del usuario {user_id}: {e}", file=sys.stderr)
        return pd.DataFrame()
    finally:
        # Restaurar el row_factory original (aunque en nuestra configuración global es None)
        conn.row_factory = original_row_factory


def get_all_training_data() -> pd.DataFrame:
    """Recupera todos los datos con 'estado_real' no nulo de la base de datos."""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()

    original_row_factory = conn.row_factory
    conn.row_factory = None

    query = f"SELECT {', '.join(['timestamp'] + FEATURE_COLUMNS + ['estado_real'])} FROM ticwatch_data WHERE estado_real IS NOT NULL"

    try:
        print("PDB: Antes de pd.read_sql_query. conn.row_factory:", conn.row_factory, file=sys.stderr)
        # Deja el pdb.set_trace() si quieres, pero por ahora vamos a quitarlo para ver el error completo
        # pdb.set_trace() # <--- COMENTA O ELIMINA ESTA LÍNEA TEMPORALMENTE

        df = pd.read_sql_query(query, conn, parse_dates=['timestamp'])
        return df
    except Exception as e:
        # --- CAMBIO IMPORTANTE AQUÍ: Imprime el traceback completo ---
        import traceback
        traceback.print_exc(file=sys.stderr) # Esto imprimirá la traza completa del error
        print(f"ERROR_CAPTURED: Error al obtener todos los datos de entrenamiento: {e}", file=sys.stderr)
        return pd.DataFrame()
    finally:
        conn.row_factory = original_row_factory


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
    except sqlite3.Error as e:
        print(f"Error al actualizar checkpoint: {e}", file=sys.stderr)

def get_user_checkpoint(user_id: str) -> Optional[dict]:
    """Recupera el último checkpoint de un usuario."""
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    # Aquí sí queremos acceso por nombre, así que lo activamos para este cursor
    cursor.row_factory = sqlite3.Row 
    try:
        cursor.execute("SELECT last_processed_timestamp, current_model_version, node_id FROM user_checkpoints WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            timestamp = datetime.fromisoformat(row['last_processed_timestamp']) if row['last_processed_timestamp'] else None
            return {
                "last_processed_timestamp": timestamp,
                "current_model_version": row['current_model_version'],
                "node_id": row['node_id']
            }
        return None
    except sqlite3.Error as e:
        print(f"Error al obtener checkpoint: {e}", file=sys.stderr)
        return None
    finally:
        # Es buena práctica resetear el row_factory del cursor si lo configuraste temporalmente
        cursor.row_factory = None

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
        print(f"Mapeo de modelo para usuario {user_id} actualizado a {model_path} ({model_type}).", file=sys.stderr)
    except sqlite3.Error as e:
        print(f"Error al actualizar mapeo de modelo: {e}", file=sys.stderr)

def get_user_model_mapping(user_id: str) -> Optional[dict]:
    """Recupera el mapeo de modelo para un usuario."""
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    # Aquí sí queremos acceso por nombre, así que lo activamos para este cursor
    cursor.row_factory = sqlite3.Row 
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
        print(f"Error al obtener mapeo de modelo: {e}", file=sys.stderr)
        return None
    finally:
        cursor.row_factory = None

if __name__ == "__main__":
    db_dir = os.path.dirname(DATABASE_URL)
    os.makedirs(db_dir, exist_ok=True)
    
    print("Inicializando base de datos...", file=sys.stderr)
    create_tables()
    print("Base de datos lista.", file=sys.stderr)