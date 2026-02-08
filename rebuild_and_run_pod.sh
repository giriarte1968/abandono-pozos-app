cat > rebuild_and_run_pod.sh << 'EOF'
#!/bin/bash

POD_NAME="pod_braco"
IMAGE_NAME="localhost/braco_worker:latest"
CONTAINER_NAME="braco_worker_pod"

echo ">>> 1. Deteniendo contenedor anterior..."
podman rm -f $CONTAINER_NAME 2>/dev/null

echo ">>> 2. RECONSTRUYENDO IMAGEN (CRÍTICO PARA APLICAR CAMBIOS)..."
# Forzamos rebuild del Containerfile.worker
podman build -t $IMAGE_NAME -f Containerfile.worker .

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Falló la construcción de la imagen."
    exit 1
fi

echo ">>> 3. Iniciando Worker DENTRO del Pod '$POD_NAME'..."
podman run -d \
  --name $CONTAINER_NAME \
  --pod $POD_NAME \
  --restart unless-stopped \
  --env-file .env \
  -e TEMPORAL_HOST=127.0.0.1 \
  -e TEMPORAL_PORT=7233 \
  -e MYSQL_HOST=127.0.0.1 \
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
    echo "✅ ÉXITO: El worker está corriendo con el código nuevo."
else
    echo "❌ ERROR: El worker se detuvo."
fi
EOF

chmod +x rebuild_and_run_pod.sh
./rebuild_and_run_pod.sh
