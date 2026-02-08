cat > deploy_prod_oci.sh << 'EOF'
#!/bin/bash

# ==============================================================================
# deploy_prod_oci.sh
# Script de despliegue consolidado para OCI (Oracle Cloud Infrastructure)
# Aplica parches de código, configuración de proxy, y networking robusto.
# ==============================================================================

set -e # Detener script si hay error

echo ">>> 1. [CODE FIX] Actualizando backend/worker.py para usar variables de entorno..."
cat > backend/worker.py << 'PYTHON_EOF'
"""Temporal Worker for P&A System"""
import asyncio
import logging
import os
from temporalio.client import Client
from temporalio.worker import Worker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main worker entry point"""
    logger.info("Starting P&A Temporal Worker...")
    
    # Connect to Temporal
    temporal_host = os.getenv("TEMPORAL_HOST", "temporal")
    temporal_port = os.getenv("TEMPORAL_PORT", "7233")
    connection_str = f"{temporal_host}:{temporal_port}"
    logger.info(f"Connecting to Temporal at {connection_str}...")
    client = await Client.connect(connection_str)
    
    logger.info("Connected to Temporal server")
    
    # TODO: Import workflows and activities when implemented
    # from backend.workflows.abandono_workflow import AbandonoPozoWorkflow
    # from backend.activities import (
    #     registrar_evento_auditoria,
    #     evaluar_habilitacion_operativa,
    #     ...
    # )
    
    # Create worker
    worker = Worker(
        client,
        task_queue="pna-tasks",
        workflows=[],  # Will add workflows here
        activities=[],  # Will add activities here
    )
    
    logger.info("Worker configured on task queue 'pna-tasks'")
    logger.info("Worker running... (press Ctrl+C to stop)")
    
    # Run worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
PYTHON_EOF
echo "✅ Code fix aplicado."


echo ">>> 2. [CONFIG] Generando configuración dinámica válida (vacía)..."
mkdir -p config/dynamicconfig
cat > config/dynamicconfig/dynamic-config.yaml << 'YAML'
# Archivo de configuración dinámica vacío para evitar errores de carga
# Temporal usará los defaults, que es lo que queremos.
YAML
echo "✅ Configuración generada."


echo ">>> 3. [INFRA] Generando podman-compose.yml con NO_PROXY..."
# Definimos las variables de exclusión de proxy que vamos a inyectar
PROXY_ENV="      - no_proxy=localhost,127.0.0.1,0.0.0.0,::1,temporal,mysql,worker,frontend,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,10.89.0.0/16"
PROXY_ENV_CAPS="      - NO_PROXY=localhost,127.0.0.1,0.0.0.0,::1,temporal,mysql,worker,frontend,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,10.89.0.0/16"

cat > podman-compose.yml << YAML
version: '3.8'

services:
  # MySQL Database (Internal only)
  mysql:
    image: docker.io/library/mysql:8.0
    user: "27:27"
    environment:
      - MYSQL_ROOT_PASSWORD=pna_root_pass
      - MYSQL_DATABASE=pna_system
      - MYSQL_USER=pna_user
      - MYSQL_PASSWORD=pna_pass
$PROXY_ENV
$PROXY_ENV_CAPS
    volumes:
      - mysql_data:/var/lib/mysql:Z
    networks:
      - pna-network

  # Temporal Server (ARM64 optimized)
  temporal:
    image: mirror.gcr.io/temporalio/auto-setup:latest
    user: "root"
    env_file:
      - .env
    environment:
      - DB=mysql8
      - MYSQL_SEEDS=mysql
      - MYSQL_USER=root
      - MYSQL_PWD=\${MYSQL_ROOT_PASSWORD}
      - MYSQL_DB=pna_system
      - VISIBILITY_DB=pna_system_visibility
      - DYNAMIC_CONFIG_FILE_PATH=config/dynamicconfig/dynamic-config.yaml
$PROXY_ENV
$PROXY_ENV_CAPS
    ports:
      - "7233:7233"
    depends_on:
      - mysql
    volumes:
      - ./config/dynamicconfig:/etc/temporal/config/dynamicconfig:Z,ro
    networks:
      - pna-network

  # Temporal Web UI
  temporal-ui:
    image: mirror.gcr.io/temporalio/ui:latest
    user: "1000:1000"
    env_file:
      - .env
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
$PROXY_ENV
$PROXY_ENV_CAPS
    ports:
      - "8080:8080"
    depends_on:
      - temporal
    networks:
      - pna-network

  # Worker (Configuración base, ejecutado manualmente en paso 6 para red compleja)
  worker:
    build:
      context: .
      dockerfile: Containerfile.worker
    user: "1000:1000"
    env_file:
      - .env
    environment:
      - TEMPORAL_HOST=temporal
      - TEMPORAL_PORT=7233
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - MYSQL_USER=pna_user
      - MYSQL_PASSWORD=pna_pass
      - MYSQL_DATABASE=pna_system
      # Deshabilitado en compose para correr manualmente
      - REPLICAS=0 
$PROXY_ENV
$PROXY_ENV_CAPS
    depends_on:
      - temporal
      - mysql
    networks:
      - pna-network
    volumes:
      - ./backend:/app/backend:ro,Z
      - ./tests:/app/tests:ro,Z
    command: python -m backend.worker

  # Streamlit Frontend
  frontend:
    build:
      context: .
      dockerfile: Containerfile.frontend
    user: "1000:1000"
    env_file:
      - .env
    environment:
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - MYSQL_USER=pna_user
      - MYSQL_PASSWORD=pna_pass
      - MYSQL_DATABASE=pna_system
$PROXY_ENV
$PROXY_ENV_CAPS
    ports:
      - "8501:8501"
    depends_on:
      - mysql
    networks:
      - pna-network
    volumes:
      - ./frontend:/app/frontend:ro,Z

networks:
  pna-network:
    driver: bridge

volumes:
  mysql_data:
    driver: local
YAML
echo "✅ podman-compose.yml generado."


echo ">>> 4. [BUILD] Reconstruyendo imágenes (Worker & Frontend)..."
podman build -t localhost/braco_worker:latest -f Containerfile.worker .
podman build -t localhost/braco_frontend:latest -f Containerfile.frontend .


echo ">>> 5. [START] Iniciando servicios core (MySQL, Temporal, Frontend)..."
# Detenemos todo primero para limpiar
podman-compose down || true
podman rm -f braco_worker_sidecar braco_worker_1 2>/dev/null || true

# Iniciamos en background
podman-compose up -d

echo "⏳ Esperando arranque de Temporal (30s)..."
current_attempt=1
max_attempts=10
sleep 5
while [ $current_attempt -le $max_attempts ]; do
    echo "Intento $current_attempt/$max_attempts..."
    if podman logs --tail 50 braco_temporal_1 2>&1 | grep -q "service started"; then
        echo "✅ Temporal SERVICE STARTED detectado."
        break
    fi
    sleep 5
    ((current_attempt++))
done

if ! podman ps | grep -q "braco_temporal_1"; then
    echo "❌ ERROR: Temporal no arrancó. Revisa logs: podman logs braco_temporal_1"
    exit 1
fi


echo ">>> 6. [WORKER] Iniciando Worker con detección inteligente de IP..."
# --- Mismo script fix_worker_final_v4.sh ---
# Buscamos contenedor Temporal
TARGET_ID=$(podman ps -q --filter "name=temporal" | grep -v $(podman ps -q --filter "name=ui") | head -n 1)

if [ -z "$TARGET_ID" ]; then
    echo "❌ ERROR CRÍTICO: No encuentro NINGÚN contenedor de Temporal corriendo."
    exit 1
fi

# Intentamos obtener la IP
TARGET_IP=$(podman inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $TARGET_ID)
TARGET_POD=$(podman inspect -f '{{.Pod}}' $TARGET_ID)

if [ -z "$TARGET_IP" ]; then
    if [ -n "$TARGET_POD" ]; then
        echo "ℹ️ Temporal está en Pod '$TARGET_POD', buscando IP del Pod..."
        POD_INFRA_ID=$(podman pod inspect $TARGET_POD -f '{{.InfraContainerID}}')
        TARGET_IP=$(podman inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $POD_INFRA_ID)
    fi
fi

if [ -z "$TARGET_IP" ]; then
    echo "⚠️ Advertencia: No pude detectar la IP automáticamente. Usando '127.0.0.1'."
    TARGET_IP="127.0.0.1"
else
    echo "✅ IP Detectada para Worker: $TARGET_IP"
fi

# Decidimos estrategia
NETWORK_ARG=""
if [ -n "$TARGET_POD" ]; then
    NETWORK_ARG="--pod $TARGET_POD"
else
    NETWORK_ARG="--network container:$TARGET_ID"
fi

podman run -d \
  --name braco_worker_sidecar \
  $NETWORK_ARG \
  --restart unless-stopped \
  --env-file .env \
  -e TEMPORAL_HOST=$TARGET_IP \
  -e TEMPORAL_PORT=7233 \
  -e MYSQL_HOST=$TARGET_IP \
  -e MYSQL_PORT=3306 \
  -e MYSQL_USER=pna_user \
  -e MYSQL_PASSWORD=pna_pass \
  -e MYSQL_DATABASE=pna_system \
  localhost/braco_worker:latest

echo "⏳ Esperando 5s..."
sleep 5

echo "Logs del Worker:"
podman logs --tail 10 braco_worker_sidecar

if podman ps | grep -q "braco_worker_sidecar"; then
    echo "✅✅ DESPLIEGUE FINALIZADO CON ÉXITO ✅✅"
else
    echo "❌ El worker falló al arrancar."
    exit 1
fi
EOF

chmod +x deploy_prod_oci.sh
./deploy_prod_oci.sh
