# Usar una imagen base oficial de Python
FROM python:3.9-slim-buster

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo requirements.txt para instalar dependencias
# Esto es más eficiente ya que Docker puede cachear esta capa
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
# Copiamos todo el contenido del directorio raíz del proyecto
# Esto es para que todos los módulos (app/, cloud_node/, etc.) sean accesibles
COPY . .

# Establecer la variable de entorno para el ID del nodo Edge
# Esto permite que cada instancia del Edge tenga un ID único para los checkpoints
ENV EDGE_NODE_ID="edge_node_default"

# Exponer el puerto en el que correrá la aplicación FastAPI
EXPOSE 8000

# Comando para ejecutar la aplicación FastAPI usando Uvicorn
# El host 0.0.0.0 es necesario para que la aplicación sea accesible desde fuera del contenedor
CMD ["uvicorn", "edge_node.server:app", "--host", "0.0.0.0", "--port", "8000"]