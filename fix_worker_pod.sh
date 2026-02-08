cat > fix_worker_pod.sh << 'EOF'
#!/bin/bash

# Configuración detectada
POD_NAME="pod_braco"
IMAGE_NAME="localhost/braco_worker:latest"
CONTAINER_NAME="braco_worker_pod"

echo ">>> 1. Limpiando intentos anteriores..."
podman rm -f $CONTAINER_NAME 2>/dev/null
podman rm -f braco_worker_manual 2>/dev/null
podman rm -f braco_worker_1 2>/dev/null

echo ">>> 2. Iniciando Worker DENTRO del Pod '$POD_NAME'..."
# Al estar en el mismo Pod, compartimos localhost con Temporal y MySQL
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

echo ">>> 3. Esperando 5s..."
sleep 5

echo ">>> 4. Verificando logs..."
podman logs --tail 20 $CONTAINER_NAME

echo ">>> 5. Verificando proceso..."
if podman ps | grep -q "$CONTAINER_NAME"; then
    echo "✅ ÉXITO: El worker está corriendo dentro del Pod."
else
    echo "❌ ERROR: El worker se detuvo."
fi
EOF

chmod +x fix_worker_pod.sh
./fix_worker_pod.sh
