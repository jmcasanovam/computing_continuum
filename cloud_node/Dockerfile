# Dockerfile para el nodo Cloud
FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación
COPY . .

# Comando para ejecutar el trainer de la Cloud (simularemos su ejecución con un script)
# Similar al Fog, esto es un placeholder.
CMD ["python", "cloud_node/trainer.py"] # Este comando es un placeholder por ahora