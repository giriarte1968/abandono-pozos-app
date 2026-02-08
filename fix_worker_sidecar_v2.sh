cat > fix_worker_sidecar_v2.sh << 'EOF'
#!/bin/bash

IMAGE_NAME="localhost/braco_worker:latest"
CONTAINER_NAME="braco_worker_sidecar"

echo ">>> 1. Buscando contenedor de Temporal..."
# Buscamos cualquier contenedor que tenga "temporal" en el nombre y NO sea ui ni worker
TARGET_ID=$(podman ps -q --filter "name=temporal" | grep -v $(podman ps -q --filter "name=ui") | head -n 1)

if [ -z "$TARGET_ID" ]; then
    echo "❌ ERROR CRÍTICO: No encuentro NINGÚN contenedor de Temporal corriendo."
    echo "Listando todos los contenedores para depuración:"
    podman ps -a
    exit 1
fi

TARGET_NAME=$(podman inspect -f '{{.Name}}' $TARGET_ID | sed 's///')
echo "✅ Encontrado objetivo: $TARGET_NAME ($TARGET_ID)"

echo ">>> 2. Limpiando intentos anteriores..."
podman rm -f $CONTAINER_NAME 2>/dev/null
podman rm -f braco_worker_pod 2>/dev/null
podman rm -f braco_worker_manual 2>/dev/null

echo ">>> 3. Iniciando Worker pegado a '$TARGET_NAME'..."
podman run -d \
  --name $CONTAINER_NAME \
  --network container:$TARGET_ID \
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
    echo "✅ ÉXITO: El worker está corriendo en modo Sidecar V2."
else
    echo "❌ ERROR: El worker se detuvo."
fi
EOF

chmod +x fix_worker_sidecar_v2.sh
./fix_worker_sidecar_v2.sh
