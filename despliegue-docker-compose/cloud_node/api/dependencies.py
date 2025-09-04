# cloud_node/api/dependencies.py
from cloud_node.model_repository import ModelRepository

# Instancia global (o Singleton) de ModelRepository para la API
# Esto asegura que todas las rutas usen la misma instancia
model_repo = ModelRepository()

def get_model_repository():
    """Dependencia para inyectar la instancia de ModelRepository."""
    return model_repo