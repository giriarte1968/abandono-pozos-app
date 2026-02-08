cat > deep_verify.sh << 'EOF'
#!/bin/bash

echo "=== 1. Verificar UPTIME (¿Se está reiniciando?) ==="
podman ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Created}}" | grep -E "worker|temporal"

echo ""
echo "=== 2. Verificar Puertos en el POD ==="
# Ejecutamos netstat dentro de Temporal para ver si 7233 está escuchando
# Usamos braco_temporal_1 porque sabemos que tiene las herramientas o al menos es el dueño del puerto
echo "Listando puertos escuchando en el contenedor Temporal:"
podman exec braco_temporal_1 netstat -tulpn | grep 7233

echo ""
echo "=== 3. Test de Conexión Python desde WORKER ==="
# Inyectamos un pequeño script python en el worker para probar conexión explícita
echo "Probando conexión TCP a 127.0.0.1:7233 desde dentro del Worker..."
podman exec braco_worker_sidecar python -c "
import socket
import sys
try:
    s = socket.create_connection(('127.0.0.1', 7233), timeout=5)
    print('✅ CONEXIÓN TCP EXITOSA a 127.0.0.1:7233')
    s.close()
except Exception as e:
    print(f'❌ ERROR DE CONEXIÓN: {e}')
    sys.exit(1)
"

echo ""
echo "=== 4. Logs MÁS recientes del Worker (últimas 5 líneas) ==="
podman logs --tail 5 braco_worker_sidecar
EOF

chmod +x deep_verify.sh
./deep_verify.sh
