cat > get_temporal_logs.sh << 'EOF'
#!/bin/bash
echo ">>> Obteniendo últimos 100 logs de Temporal (braco_temporal_1)..."
podman logs --tail 100 braco_temporal_1
EOF
chmod +x get_temporal_logs.sh
./get_temporal_logs.sh
