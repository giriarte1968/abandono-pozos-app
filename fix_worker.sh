cat > fix_worker.sh << 'EOF'
#!/bin/bash

echo ">>> 1. Reconstruyendo Worker (asegurando última versión)..."
podman-compose build worker

echo ""
echo ">>> 2. Iniciando Worker (modo detached)..."
# Usamos --force-recreate para asegurar que tome la nueva imagen y configuración
podman-compose up -d --force-recreate worker

echo ""
echo ">>> 3. Esperando arranque (10s)..."
sleep 10

echo ""
echo ">>> 4. Verificando estado..."
if podman ps | grep -q "worker"; then
    echo "✅ WORKER ESTÁ CORRIENDO!"
    echo "--- Últimos logs del worker ---"
    podman logs --tail 20 $(podman ps -q --filter "name=worker" | head -n 1)
else
    echo "❌ WORKER FALLÓ AL INICIAR"
    echo "--- Logs de inspección (si existe contenedor muerto) ---"
    podman logs --tail 50 $(podman ps -a -q --filter "name=worker" | head -n 1) 2>/dev/null
fi
EOF

chmod +x fix_worker.sh
./fix_worker.sh
