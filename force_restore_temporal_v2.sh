cat > force_restore_temporal_v2.sh << 'EOF'
#!/bin/bash

echo ">>> 1. Asegurando archivo de configuración..."
mkdir -p config/dynamicconfig
cat > config/dynamicconfig/development-sql.yaml << 'YAML'
persistence:
  defaultStore: default
  visibilityStore: visibility
  numHistoryShards: 1
  datastores:
    default:
      sql:
        driver: mysql8
        host: mysql
        port: 3306
        database: pna_system
        user: root
        password: pna_root_pass
        connectAttributes:
          "read-only": "true"
          "txIsolation": "READ-COMMITTED"
    visibility:
      sql:
        driver: mysql8
        host: mysql
        port: 3306
        database: pna_system
        databaseNamePrefix: pna_system_visibility
        user: root
        password: pna_root_pass
        connectAttributes:
          "read-only": "true"
          "txIsolation": "READ-COMMITTED"

  history:
    numHistoryShards: 1

global:
  membership:
    maxJoinDuration: 30s
  metrics:
    prometheus:
      address: "0.0.0.0:9090"
YAML

echo ">>> 2. FORZANDO sobrescritura de podman-compose.yml (Corrección de Volumen)..."
# El script anterior falló al detectar si ya existía la config.
# Esta vez sobrescribimos sin preguntar para asegurar que el volumen esté ahí.
cat > podman-compose.yml << 'YAML'
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
      - MYSQL_PWD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DB=pna_system
      - VISIBILITY_DB=pna_system_visibility
      - DYNAMIC_CONFIG_FILE_PATH=config/dynamicconfig/development-sql.yaml
    ports:
      - "7233:7233"
    depends_on:
      - mysql
    volumes:
      # ESTA ES LA LÍNEA CRÍTICA QUE FALTABA
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
    ports:
      - "8080:8080"
    depends_on:
      - temporal
    networks:
      - pna-network

  # Python Worker (OCI ARM64 compliant) -> Lo dejamos aquí para referencia, pero lo corremos manual
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
    depends_on:
      - temporal
      - mysql
    networks:
      - pna-network
    volumes:
      - ./backend:/app/backend:ro,Z
      - ./tests:/app/tests:ro,Z
    command: python -m backend.worker

  # Streamlit Frontend (OCI ARM64 compliant)
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

echo ">>> 3. Limpiando contenedor Temporal roto..."
podman rm -f braco_temporal_1 2>/dev/null

echo ">>> 4. Levantando Temporal (Up -d)..."
podman-compose up -d temporal

echo ">>> 5. Esperando arranque (15s)..."
current_attempt=1
max_attempts=6
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
echo ">>> 6. Lanzando Worker Sidecar (V2)..."
./fix_worker_sidecar_v2.sh
EOF

chmod +x force_restore_temporal_v2.sh
./force_restore_temporal_v2.sh
