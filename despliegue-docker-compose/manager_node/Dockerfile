# Imagen base
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Establecer variable de entorno PYTHONPATH
ENV PYTHONPATH=/app

# Copiar archivos
COPY requirements_manager.txt .
RUN pip install --no-cache-dir -r requirements_manager.txt

COPY . .

# Comando para ejecutar la API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
