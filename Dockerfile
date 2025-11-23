FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para PyMuPDF y otras bibliotecas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libpoppler-cpp-dev \
 && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar PyMuPDF explícitamente para asegurar que se instale correctamente
RUN pip install --no-cache-dir PyMuPDF==1.23.8

# Copiar el resto de la aplicación
COPY . .

# Configuración de variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Exponer el puerto que usa la aplicación
EXPOSE $PORT

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]
