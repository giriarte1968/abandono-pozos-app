cat > fix_proxy_issue.sh << 'EOF'
#!/bin/bash

echo ">>> 🚨 ALERTA: Detectado Proxy Squid interceptando tráfico interno."
echo ">>> Configurando NO_PROXY para evitar que Temporal se bloquee a sí mismo..."

# Definimos las variables de exclusión de proxy que vamos a inyectar
# Incluimos localhost, IPs de loopback, nombres de servicio y rangos de red privados comunes
PROXY_ENV="      - no_proxy=localhost,127.0.0.1,0.0.0.0,::1,temporal,mysql,worker,frontend,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,10.89.0.0/16"
PROXY_ENV_CAPS="      - NO_PROXY=localhost,127.0.0.1,0.0.0.0,::1,temporal,mysql,worker,frontend,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,10.89.0.0/16"

# Vamos a reescribir podman-compose.yml agregando estas variables a TODOS los servicios
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

  # Worker (Sidecar mode preferred via script, but kept here for definition)
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

echo ">>> 2. Reiniciando TODO el stack..."
podman-compose down
podman rm -f braco_temporal_1 braco_mysql_1 braco_worker_sidecar 2>/dev/null
podman-compose up -d

echo ">>> 3. Esperando arranque de Temporal (30s)..."
current_attempt=1
max_attempts=10
sleep 5
while [ $current_attempt -le $max_attempts ]; do
    echo "Intento $current_attempt/$max_attempts..."
    if podman logs --tail 50 braco_temporal_1 2>&1 | grep -q "service started"; then
        echo "✅ Temporal SERVICE STARTED detectado en logs."
        break
    fi
    sleep 5
    ((current_attempt++))
done

if ! podman ps | grep -q "braco_temporal_1"; then
    echo "❌ ERROR: Temporal no arrancó. Logs:"
    podman logs --tail 20 braco_temporal_1
    exit 1
fi

echo ""
echo ">>> 4. Lanzando Worker Sidecar (V3 - Pod Aware)..."
./fix_worker_sidecar_v3.sh
EOF

chmod +x fix_proxy_issue.sh
./fix_proxy_issue.sh
