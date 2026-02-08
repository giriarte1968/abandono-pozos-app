cat > check_final_status.sh << 'EOF'
#!/bin/bash

echo "=== 1. Estado de Contenedores ==="
# Usamos formato tabla para ver uptime y status
podman ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== 2. Logs recientes de Temporal (Errors?) ==="
podman logs --tail 50 braco_temporal_1

echo ""
echo "=== 3. Logs recientes del Worker (Looping?) ==="
podman logs --tail 20 braco_worker_sidecar
EOF

chmod +x check_final_status.sh
./check_final_status.sh
