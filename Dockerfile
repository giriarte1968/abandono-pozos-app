# AbandonPro - Dockerfile para DigitalOcean App Platform
# Servicio: Frontend Streamlit

FROM python:3.11-slim

# Evitar buffering de Python (mejor para logs en producción)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Configuración de Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_HEADLESS=true

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema (incluyendo librerías para mysqlclient)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    pkg-config \
    default-libmysqlclient-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (optimización de cache)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código
COPY . .

# Health check para DigitalOcean
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Exponer puerto 8501 (Streamlit default)
EXPOSE 8501

# Comando de inicio
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
