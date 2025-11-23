FROM python:3.10-slim

# Dependencias básicas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de la aplicación
WORKDIR /app

# Copiar requirements.txt e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar PyMuPDF explícitamente
RUN pip install --no-cache-dir pymupdf

# Instalar gunicorn explícitamente
RUN pip install --no-cache-dir gunicorn

# Copiar el resto de archivos
COPY . .

# Puerto para Render
ENV PORT=10000
EXPOSE $PORT

# Comando para ejecutar la app
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "app:app"]
