cat > fix_worker_sidecar_v3.sh << 'EOF'
#!/bin/bash

IMAGE_NAME="localhost/braco_worker:latest"
CONTAINER_NAME="braco_worker_sidecar"

echo ">>> 1. Buscando contenedor de Temporal..."
# Buscamos cualquier contenedor que tenga "temporal" en el nombre y NO sea ui ni worker
IDS=$(podman ps -q --filter "name=temporal")
UI_ID=$(podman ps -q --filter "name=ui")
TARGET_ID=""

for id in $IDS; do
    if [ "$id" != "$UI_ID" ]; then
        TARGET_ID=$id
        break
    fi
done

if [ -z "$TARGET_ID" ]; then
    echo "❌ ERROR CRÍTICO: No encuentro NINGÚN contenedor de Temporal corriendo."
    podman ps -a
    exit 1
fi

TARGET_NAME=$(podman inspect -f '{{.Name}}' $TARGET_ID | sed 's/\///')
TARGET_POD=$(podman inspect -f '{{.Pod}}' $TARGET_ID)

echo "✅ Encontrado objetivo: $TARGET_NAME ($TARGET_ID)"

echo ">>> 2. Limpiando intentos anteriores..."
podman rm -f $CONTAINER_NAME 2>/dev/null
podman rm -f braco_worker_pod 2>/dev/null
podman rm -f braco_worker_manual 2>/dev/null

echo ">>> 3. Determinando estrategia de conexión..."
NETWORK_ARG=""

if [ -n "$TARGET_POD" ]; then
    echo "ℹ️ El objetivo está DENTRO de un POD ($TARGET_POD)."
    echo "👉 Estrategia: Unirse al POD."
    NETWORK_ARG="--pod $TARGET_POD"
else
    echo "ℹ️ El objetivo es un contenedor suelto."
    echo "👉 Estrategia: Unirse al namespace de RED del contenedor (Sidecar)."
    NETWORK_ARG="--network container:$TARGET_ID"
fi

echo ">>> 4. Iniciando Worker..."
podman run -d \
  --name $CONTAINER_NAME \
  $NETWORK_ARG \
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

echo ">>> 5. Esperando 5s..."
sleep 5

echo ">>> 6. Verificando logs..."
podman logs --tail 20 $CONTAINER_NAME

echo ">>> 7. Verificando proceso..."
if podman ps | grep -q "$CONTAINER_NAME"; then
    echo "✅ ÉXITO: El worker está corriendo."
else
    echo "❌ ERROR: El worker se detuvo."
fi
EOF

chmod +x fix_worker_sidecar_v3.sh
./fix_worker_sidecar_v3.sh
