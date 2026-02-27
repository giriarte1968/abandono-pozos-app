#!/bin/bash

echo "=== 1. Verificar UPTIME (Contenedoresactivos) ==="
docker compose ps

echo ""
echo "=== 2. Verificar Puertos en Temporal ==="
echo "Listando puertos escuchando en el contenedor Temporal (7233):"
docker compose exec temporal netstat -tulpn 2>/dev/null | grep 7233 || echo "Netstat no disponible, verificando vía socket..."

echo ""
echo "=== 3. Test de Conexión Python desde WORKER ==="
echo "Probando conexión TCP a temporal:7233 desde dentro del Worker..."
docker compose exec worker python -c "
import socket
import sys
try:
    # Usamos 'temporal' como host porque estamos en la red de docker compose
    s = socket.create_connection(('temporal', 7233), timeout=5)
    print('✅ CONEXIÓN TCP EXITOSA a temporal:7233')
    s.close()
except Exception as e:
    print(f'❌ ERROR DE CONEXIÓN: {e}')
    sys.exit(1)
"

echo ""
echo "=== 4. Logs MÁS recientes del Worker (últimas 10 líneas) ==="
docker compose logs --tail 10 worker
