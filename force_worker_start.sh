cat > force_worker_start.sh << 'EOF'
#!/bin/bash

echo ">>> 1. Limpiando intentos anteriores fallidos..."
podman rm -f braco_worker_1 2>/dev/null

echo ">>> 2. Construyendo imagen..."
podman-compose build worker

echo ">>> 3. Iniciando Worker (SIN RECREAR DEPENDENCIAS)..."
# --no-deps: No intenta arrancar/recrear mysql o temporal
# --force-recreate: Fuerza a crear el contenedor del worker nuevo
podman-compose up -d --no-deps --force-recreate worker

echo ">>> 4. Esperando 5s..."
sleep 5

echo ">>> 5. Verificando logs..."
podman logs --tail 20 braco_worker_1

echo ">>> 6. Verificando proceso..."
if podman ps | grep -q "worker"; then
    echo "✅ ÉXITO: El worker está corriendo."
else
    echo "❌ ERROR: El worker se detuvo inmediatamente."
fi
EOF

chmod +x force_worker_start.sh
./force_worker_start.sh
