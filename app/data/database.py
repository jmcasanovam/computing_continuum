import psycopg2
import pandas as pd
from app.config import DATABASE_URL, FEATURE_COLUMNS
from datetime import datetime
import os
from typing import Optional
import sys # Importar sys para stderr


def get_db_connection():
    """
    Obtiene y devuelve una conexión a la base de datos PostgreSQL.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        # Para PostgreSQL y pandas, no es necesario configurar row_factory = None.
        # Pandas lo gestiona correctamente.
        return conn
    except psycopg2.Error as e:
        print(f"ERROR: No se pudo conectar a la base de datos PostgreSQL usando {DATABASE_URL}: {e}", file=sys.stderr)
        # En un entorno real, podrías querer reintentar o registrar el error de forma más robusta.
        return None

def create_tables():
    """
    Crea las tablas necesarias en la base de datos PostgreSQL si no existen.
    """
    conn = get_db_connection()
    if conn is None:
        print("No se pudo obtener conexión a la base de datos para crear tablas.", file=sys.stderr)
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticwatch_data (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
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
                    estado_real TEXT,
                    ticwatchconnected BOOLEAN, -- <-- ¡AÑADE ESTA LÍNEA!
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # ... (el resto de tus CREATE TABLE son los mismos) ...
        conn.commit()
        print("Tablas de la base de datos creadas/verificadas (PostgreSQL).", file=sys.stderr)
    except psycopg2.Error as e:
        print(f"ERROR al crear tablas en PostgreSQL: {e}", file=sys.stderr)
    finally:
        if conn:
            conn.close()

def insert_ticwatch_data(data: dict):
    """
    Inserta un registro de datos del TicWatch en la tabla ticwatch_data de PostgreSQL.
    """
    conn = get_db_connection()
    if conn is None:
        return

    try:
        with conn.cursor() as cursor:
            columns = [
                "session_id", "user_id", "timestamp",
                "tic_accx", "tic_accy", "tic_accz",
                "tic_acclx", "tic_accly", "tic_acclz",
                "tic_girx", "tic_giry", "tic_girz",
                "tic_hrppg", "tic_step",
                "predicted_state", "estado_real" # Asumiendo que ticwatchconnected no se inserta si no está en el dict
            ]
            
            # Asegurarse de que 'timestamp' sea un objeto datetime para psycopg2
            timestamp_val = data['timeStamp']
            if isinstance(timestamp_val, str):
                try:
                    # Intenta parsear el formato que genera generate_initial_model
                    timestamp_val = datetime.strptime(timestamp_val, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    print(f"WARNING: Formato de timestamp inesperado para '{timestamp_val}'. "
                          "No se pudo parsear. Asegúrate de que el formato sea '%Y-%m-%d %H:%M:%S'.", file=sys.stderr)
                    # En producción, esto podría ser un error fatal o requerir un manejo más sofisticado.
                    return # No inserta el dato si el timestamp es inválido.
            
            # Aseguramos que todas las columnas en 'columns' estén presentes en 'data' o sean None
            # También debemos manejar 'ticwatchconnected' si se va a insertar.
            # Agregamos 'ticwatchconnected' si es necesario
            if 'ticwatchconnected' in data and 'ticwatchconnected' not in columns:
                columns.append('ticwatchconnected')

            values = []
            for col in columns:
                if col == 'timestamp':
                    values.append(timestamp_val)
                elif col == 'ticwatchconnected':
                    values.append(data.get(col, False)) # Default a False si no está
                else:
                    values.append(data.get(col))

            placeholders = ', '.join(['%s'] * len(columns)) # PostgreSQL usa %s para placeholders
            
            cursor.execute(f"INSERT INTO ticwatch_data ({', '.join(columns)}) VALUES ({placeholders})", tuple(values))
        conn.commit()
    except psycopg2.Error as e:
        print(f"ERROR al insertar datos en PostgreSQL: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
    finally:
        if conn:
            conn.close()

def get_all_training_data() -> pd.DataFrame:
    """
    Recupera todos los datos con 'estado_real' no nulo de la base de datos PostgreSQL.
    """
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()

    # Construir la lista de columnas para la consulta
    cols_to_select = ['timestamp'] + FEATURE_COLUMNS + ['estado_real']
    query = f"SELECT {', '.join(cols_to_select)} FROM ticwatch_data WHERE estado_real IS NOT NULL"
    
    try:
        print("PDB: Antes de pd.read_sql_query. conn.row_factory: N/A (para psycopg2)", file=sys.stderr)
        # pd.read_sql_query funciona bien con conexiones psycopg2 y automáticamente maneja el row_factory
        df = pd.read_sql_query(query, conn, parse_dates=['timestamp'])
        return df
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(f"ERROR_CAPTURED: Error al obtener todos los datos de entrenamiento de PostgreSQL: {e}", file=sys.stderr)
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def get_user_data(user_id: str, limit: Optional[int] = None) -> pd.DataFrame:
    """Recupera datos de un usuario específico de la base de datos PostgreSQL."""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    
    cols_to_select = ['timestamp'] + FEATURE_COLUMNS + ['estado_real']
    query = f"SELECT {', '.join(cols_to_select)} FROM ticwatch_data WHERE user_id = %s"
    
    params = [user_id]
    if limit:
        query += f" ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
    
    try:
        # pd.read_sql_query con psycopg2 y %s para parámetros
        df = pd.read_sql_query(query, conn, params=tuple(params), parse_dates=['timestamp'])
        return df
    except Exception as e:
        print(f"Error al obtener datos del usuario {user_id} de PostgreSQL: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def update_user_checkpoint(user_id: str, timestamp: datetime, model_version: str, node_id: str):
    """Actualiza el checkpoint de un usuario en PostgreSQL."""
    conn = get_db_connection()
    if conn is None:
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_checkpoints (user_id, last_processed_timestamp, current_model_version, node_id, updated_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    last_processed_timestamp = EXCLUDED.last_processed_timestamp,
                    current_model_version = EXCLUDED.current_model_version,
                    node_id = EXCLUDED.node_id,
                    updated_at = CURRENT_TIMESTAMP;
            """, (user_id, timestamp, model_version, node_id)) # psycopg2 maneja datetime directamente
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error al actualizar checkpoint en PostgreSQL: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
    finally:
        if conn:
            conn.close()

def get_user_checkpoint(user_id: str) -> Optional[dict]:
    """Recupera el último checkpoint de un usuario de PostgreSQL."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT last_processed_timestamp, current_model_version, node_id FROM user_checkpoints WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                # row[0] es last_processed_timestamp, ya será un objeto datetime
                return {
                    "last_processed_timestamp": row[0], # Ya es datetime de psycopg2
                    "current_model_version": row[1],
                    "node_id": row[2]
                }
            return None
    except psycopg2.Error as e:
        print(f"Error al obtener checkpoint de PostgreSQL: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None
    finally:
        if conn:
            conn.close()

def update_user_model_mapping(user_id: str, model_path: str, model_type: str):
    """Actualiza el mapeo de usuario a modelo activo en PostgreSQL."""
    conn = get_db_connection()
    if conn is None:
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_model_mapping (user_id, model_path, model_type, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    model_path = EXCLUDED.model_path,
                    model_type = EXCLUDED.model_type,
                    updated_at = CURRENT_TIMESTAMP;
            """, (user_id, model_path, model_type))
        conn.commit()
        print(f"Mapeo de modelo para usuario {user_id} actualizado a {model_path} ({model_type}).", file=sys.stderr)
    except psycopg2.Error as e:
        print(f"Error al actualizar mapeo de modelo en PostgreSQL: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
    finally:
        if conn:
            conn.close()

def get_user_model_mapping(user_id: str) -> Optional[dict]:
    """Recupera el mapeo de modelo para un usuario de PostgreSQL."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT model_path, model_type FROM user_model_mapping WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "model_path": row[0],
                    "model_type": row[1]
                }
            return None
    except psycopg2.Error as e:
        print(f"Error al obtener mapeo de modelo de PostgreSQL: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    
    print("Inicializando base de datos (PostgreSQL)...", file=sys.stderr)
    create_tables()
    print("Base de datos PostgreSQL lista.", file=sys.stderr)