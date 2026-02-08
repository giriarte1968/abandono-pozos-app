cat > fix_worker_final_v4.sh << 'EOF'
#!/bin/bash

# --- 1. Detectar contenedor de Temporal ---
echo ">>> 1. Buscando IP de Temporal..."
# Primero intentamos encontrar el contenedor
TARGET_ID=$(podman ps -q --filter "name=temporal" | grep -v $(podman ps -q --filter "name=ui") | head -n 1)

if [ -z "$TARGET_ID" ]; then
    echo "❌ ERROR CRÍTICO: No encuentro NINGÚN contenedor de Temporal corriendo."
    exit 1
fi

# --- 2. Obtener IP y configurar Estrategia ---
# Intentamos obtener la IP del contenedor
# Nota: Si está en un Pod, a veces la IP está en el Pod Infra Container, pero 'podman inspect' suele resolverlo bien
TARGET_IP=$(podman inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $TARGET_ID)

# Si falla, intentamos obtener el nombre del Pod
TARGET_POD=$(podman inspect -f '{{.Pod}}' $TARGET_ID)

if [ -z "$TARGET_IP" ]; then
    # Si no tiene IP directa (porque usa --net host o algo raro), intentamos inspeccionar el pod
    if [ -n "$TARGET_POD" ]; then
        echo "ℹ️ Temporal está en Pod '$TARGET_POD', buscando IP del Pod..."
        # La IP del pod suele ser la del contenedor 'infra'
        POD_INFRA_ID=$(podman pod inspect $TARGET_POD -f '{{.InfraContainerID}}')
        TARGET_IP=$(podman inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $POD_INFRA_ID)
    fi
fi

if [ -z "$TARGET_IP" ]; then
    echo "⚠️ Advertencia: No pude detectar la IP automáticamente. Usando '127.0.0.1' como fallback (puede fallar)."
    TARGET_IP="127.0.0.1"
else
    echo "✅ IP Detectada: $TARGET_IP"
fi


echo ">>> 3. Limpiando worker anterior..."
podman rm -f braco_worker_sidecar 2>/dev/null

echo ">>> 4. Iniciando Worker conectado a $TARGET_IP:7233..."

# Decidimos si usar --pod o --network container
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

echo ">>> 5. Esperando 5s..."
sleep 5

echo ">>> 6. Verificando logs..."
podman logs --tail 20 braco_worker_sidecar

echo ">>> 7. Verificando proceso..."
if podman ps | grep -q "braco_worker_sidecar"; then
    echo "✅ ÉXITO: El worker está CORRIENDO y CONECTADO."
else
    echo "❌ ERROR: El worker se detuvo."
fi
EOF

chmod +x fix_worker_final_v4.sh
./fix_worker_final_v4.sh
