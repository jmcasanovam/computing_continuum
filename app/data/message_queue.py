import json
import os
from app.config import MESSAGE_QUEUE_FILE
import threading

# Asegurarse de que el directorio del archivo de la cola exista
queue_dir = os.path.dirname(MESSAGE_QUEUE_FILE)
os.makedirs(queue_dir, exist_ok=True)

# Lock para asegurar que las operaciones de lectura/escritura en el archivo son seguras
# en un entorno multithread/multiprocess (aunque solo simularemos un productor por ahora)
queue_lock = threading.Lock()

def _read_queue():
    """Función interna para leer el contenido actual de la cola."""
    if not os.path.exists(MESSAGE_QUEUE_FILE):
        return []
    with open(MESSAGE_QUEUE_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return [] # Archivo vacío o corrupto

def _write_queue(data):
    """Función interna para escribir el contenido completo en la cola."""
    with open(MESSAGE_QUEUE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def publish_message(message: dict):
    """Publica un mensaje en la cola (añade al final)."""
    with queue_lock:
        queue_content = _read_queue()
        queue_content.append(message)
        _write_queue(queue_content)
    # print(f"Mensaje publicado en la cola: {message.get('user_id')} - {message.get('timestamp')}")

def consume_messages() -> list:
    """Consume todos los mensajes de la cola (vacía el archivo)."""
    with queue_lock:
        queue_content = _read_queue()
        _write_queue([]) # Vaciar la cola después de consumir
    # print(f"Consumidos {len(queue_content)} mensajes de la cola.")
    return queue_content