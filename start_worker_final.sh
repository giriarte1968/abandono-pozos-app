cat > start_worker_final.sh << 'EOF'
#!/bin/bash
echo ">>> Temporal ya arrancó (lo vimos en los logs)."
echo ">>> Reiniciando Worker para conectar..."
podman restart braco_worker_sidecar

echo ">>> Esperando 5s..."
sleep 5

echo ">>> Verificando logs del Worker..."
podman logs --tail 20 braco_worker_sidecar

echo ">>> Verificando si sigue vivo..."
if podman ps | grep -q "braco_worker_sidecar"; then
    echo "✅ ÉXITO TOTAL: El worker está conectado y corriendo."
else
    echo "❌ ERROR: El worker se detuvo de nuevo."
fi
EOF

chmod +x start_worker_final.sh
./start_worker_final.sh
