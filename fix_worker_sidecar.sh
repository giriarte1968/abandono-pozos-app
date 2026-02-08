cat > fix_worker_sidecar.sh << 'EOF'
#!/bin/bash

# Estrategia: "Sidecar"
# Nos unimos al namespace de red del contenedor de Temporal (braco_temporal_1).
# Esto garantiza que 127.0.0.1 sea el mismo para ambos.

TARGET_CONTAINER="braco_temporal_1"
IMAGE_NAME="localhost/braco_worker:latest"
CONTAINER_NAME="braco_worker_sidecar"

echo ">>> 1. Limpiando intentos anteriores..."
podman rm -f $CONTAINER_NAME 2>/dev/null
podman rm -f braco_worker_pod 2>/dev/null
podman rm -f braco_worker_manual 2>/dev/null

echo ">>> 2. Verificando que Temporal exista..."
if ! podman ps | grep -q "$TARGET_CONTAINER"; then
    echo "❌ ERROR: No encuentro el contenedor '$TARGET_CONTAINER'. ¿Está corriendo?"
    exit 1
fi

echo ">>> 3. Iniciando Worker pegado a '$TARGET_CONTAINER'..."
podman run -d \
  --name $CONTAINER_NAME \
  --network container:$TARGET_CONTAINER \
  --restart unless-stopped \
  --env-file .env \
  -e TEMPORAL_HOST=127.0.0.1 \
  -e TEMPORAL_PORT=7233 \
  -e MYSQL_HOST=mysql \
  -e MYSQL_PORT=3306 \
  -e MYSQL_USER=pna_user \
  -e MYSQL_PASSWORD=pna_pass \
  -e MYSQL_DATABASE=pna_system \
  $IMAGE_NAME

echo ">>> 4. Esperando 5s..."
sleep 5

echo ">>> 5. Verificando logs..."
podman logs --tail 20 $CONTAINER_NAME

echo ">>> 6. Verificando proceso..."
if podman ps | grep -q "$CONTAINER_NAME"; then
    echo "✅ ÉXITO: El worker está corriendo en modo Sidecar."
else
    echo "❌ ERROR: El worker se detuvo."
fi
EOF

chmod +x fix_worker_sidecar.sh
./fix_worker_sidecar.sh
