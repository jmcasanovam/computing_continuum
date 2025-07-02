# Dockerfile para el nodo Fog
FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación para que todos los módulos sean accesibles
COPY . .

# Comando para ejecutar el trainer del Fog (simularemos su ejecución con un script)
# Este Dockerfile solo prepara el entorno. La ejecución real se hará vía docker-compose o scripts.
# Puedes cambiar esto a un ENTRYPOINT si el contenedor debe ejecutar una tarea única y salir.
CMD ["python", "fog_node/trainer.py"] # Este comando es un placeholder por ahora