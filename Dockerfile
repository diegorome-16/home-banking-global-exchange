# Usa una imagen base de Python
FROM python:3.12-slim

# Evita que Python guarde bytecode y buffers en salida
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de dependencias
COPY requirements.txt /app/

# Instala dependencias del sistema y las librerías de Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copia el resto del proyecto
COPY . /app/

# Expone el puerto interno del contenedor
EXPOSE 8001

# Comando para ejecutar Gunicorn (ajusta el nombre de tu módulo WSGI)
CMD ["gunicorn", "-b", "0.0.0.0:8001", "home_banking.wsgi"]
