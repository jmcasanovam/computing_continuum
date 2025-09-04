# Usa una imagen base de Python oficial
FROM python:3.9-slim

# Instalar curl, que es necesario para descargar kubectl
RUN apt-get update && apt-get install -y curl

# Descargar y instalar kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Establece el directorio de trabajo
WORKDIR /app

# Copia los requirements.txt e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la aplicación
COPY ./app /app/app

# Expone el puerto 8001 para la API del manager
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
