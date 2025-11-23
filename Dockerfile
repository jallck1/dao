FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema mínimas (si alguna librería lo requiere, se puede ampliar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run pasa el puerto en la variable de entorno PORT
ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
