cat > fix_temporal_config_v3.sh << 'EOF'
#!/bin/bash

echo ">>> 1. Corrigiendo configuración de Temporal (eliminando DYNAMIC_CONFIG_FILE_PATH incorrecto)..."
# Usamos sed para eliminar la línea de DYNAMIC_CONFIG_FILE_PATH y su valor
# También eliminamos el volumen asociado para limpiar la config
sed -i '/DYNAMIC_CONFIG_FILE_PATH/d' podman-compose.yml
sed -i '/config\/dynamicconfig\/development-sql.yaml/d' podman-compose.yml
sed -i '/\.\/config\/dynamicconfig:\/etc\/temporal\/config\/dynamicconfig:Z,ro/d' podman-compose.yml

echo "✅ Configuración actualizada en podman-compose.yml."

echo ""
echo ">>> 2. Eliminando contenedor Temporal anterior..."
podman rm -f braco_temporal_1 2>/dev/null

echo ">>> 3. Levantando Temporal (Up -d) con configuración limpia..."
podman-compose up -d temporal

echo ">>> 4. Esperando arranque (20s)..."
current_attempt=1
max_attempts=8
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
echo ">>> 5. Lanzando Worker Sidecar (V2)..."
./fix_worker_sidecar_v2.sh
EOF

chmod +x fix_temporal_config_v3.sh
./fix_temporal_config_v3.sh
