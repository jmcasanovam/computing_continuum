# Dockerfile para el nodo Fog
FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación para que todos los módulos sean accesibles
COPY . .

CMD ["python", "fog_node/trainer.py"] # Este comando es un placeholder por ahora