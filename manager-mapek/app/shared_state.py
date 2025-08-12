# app/shared_state.py

import threading
from typing import Dict

# Un lock para asegurar la seguridad de los hilos al modificar el contador
user_count_lock = threading.Lock()

# Diccionario para almacenar el conteo de usuarios por IP de nodo
active_users_per_node: Dict[str, int] = {}