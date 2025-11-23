FROM python:3.10

# Instalar dependencias del sistema necesarias para PyMuPDF y Poppler
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de la aplicación
WORKDIR /app

# Copiar requirements.txt e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar gunicorn explícitamente
RUN pip install --no-cache-dir gunicorn

# Copiar el resto de archivos
COPY . .

# Render necesita exponer el puerto vía PORT
ENV PORT=10000
EXPOSE ${PORT}

# Comando para ejecutar la app
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "app:app"]
