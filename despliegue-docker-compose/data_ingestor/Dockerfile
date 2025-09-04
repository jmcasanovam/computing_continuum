FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Establecer PYTHONPATH para que Python encuentre el paquete 'app'
ENV PYTHONPATH=/app

# Comando para ejecutar el script del ingestor
CMD ["python", "data_ingestor/ingestor.py"]