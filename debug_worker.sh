cat > debug_worker.sh << 'EOF'
#!/bin/bash
echo ">>> 1. Intentando construir el worker..."
podman-compose build worker

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Falló la construcción del worker."
    exit 1
fi

echo ""
echo ">>> 2. Intentando arrancar el worker en primer plano para ver errores..."
# Usamos run --rm para que no se acumule, y service-ports para que use la red definida
podman-compose run --rm --service-ports worker
EOF

chmod +x debug_worker.sh
./debug_worker.sh
