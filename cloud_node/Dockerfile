# Dockerfile para el nodo Cloud
FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación
COPY . .

# Comando para ejecutar el trainer de la Cloud 
CMD ["python", "scripts/run_cloud_trainer_init_and_loop.py"]