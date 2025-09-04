from pydantic import BaseModel

class ModelMappingUpdate(BaseModel):
    """
    Esquema para la actualización del mapeo de modelo de usuario.
    """
    model_path: str
    model_type: str