cat > manual_fix_worker.sh << 'EOF'
#!/bin/bash

# Configuración detectada
NETWORK_NAME="braco_pna-network"
IMAGE_NAME="localhost/braco_worker:latest"
CONTAINER_NAME="braco_worker_manual"

echo ">>> 1. Eliminando versiones anteriores manuales..."
podman rm -f $CONTAINER_NAME 2>/dev/null
podman rm -f braco_worker_1 2>/dev/null

echo ">>> 2. Iniciando Worker manualmente en la red '$NETWORK_NAME'..."
# Inyectamos las variables explícitamente para asegurar conexión
podman run -d \
  --name $CONTAINER_NAME \
  --network $NETWORK_NAME \
  --restart unless-stopped \
  --env-file .env \
  -e TEMPORAL_HOST=temporal \
  -e TEMPORAL_PORT=7233 \
  -e MYSQL_HOST=mysql \
  -e MYSQL_PORT=3306 \
  -e MYSQL_USER=pna_user \
  -e MYSQL_PASSWORD=pna_pass \
  -e MYSQL_DATABASE=pna_system \
  $IMAGE_NAME

echo ">>> 3. Esperando 5s..."
sleep 5

echo ">>> 4. Verificando logs..."
podman logs --tail 20 $CONTAINER_NAME

echo ">>> 5. Verificando si sigue corriendo..."
if podman ps | grep -q "$CONTAINER_NAME"; then
    echo "✅ ÉXITO: El worker está corriendo y conectado a la red."
else
    echo "❌ ERROR: El worker se detuvo."
fi
EOF

chmod +x manual_fix_worker.sh
./manual_fix_worker.sh
