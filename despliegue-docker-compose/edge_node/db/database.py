from dotenv import load_dotenv
import os
from pymongo import MongoClient

# Cargar variables de entorno desde el archivo .env
load_dotenv()
# Configuración de la conexión a MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://192.168.1.141:27012/")  # Valor por defecto si no se encuentra la variable de entorno


# Reemplaza la URI con la de tu servidor MongoDB
# MONGO_URI = "mongodb://192.168.1.141:27012/"
DATABASE_NAME = "userdatarecovery"

# Crear cliente y conectar
client = MongoClient(MONGO_URI)

# Seleccionar base de datos
db = client[DATABASE_NAME]

# Exportar la colección TicWatch
ticwatch_collection = db["TicWatch"]

def probar_bd():
    try:
        # Probar la conexión listando las colecciones
        print("Colecciones en la base de datos:", db.list_collection_names())
    except Exception as e:
        print("Error al conectar o listar colecciones:", e)
    finally:
        # Cerrar la conexión cuando termines
        client.close()