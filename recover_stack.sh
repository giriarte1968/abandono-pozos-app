cat > recover_stack.sh << 'EOF'
#!/bin/bash

echo ">>> 🚨 Temporal se cayó. Analizando logs (últimas 20 líneas)..."
podman logs --tail 20 braco_temporal_1

echo ""
echo ">>> 1. Reiniciando Temporal..."
podman start braco_temporal_1

echo ">>> 2. Verificando estado (esperando 10s)..."
sleep 10
if podman ps | grep -q "braco_temporal_1"; then
    echo "✅ Temporal ha vuelto a la vida."
else
    echo "❌ ERROR: Temporal falló al arrancar de nuevo. Revisa los logs arriba."
    podman logs --tail 20 braco_temporal_1
    exit 1
fi

echo ""
echo ">>> 3. Ejecutando Sidecar Worker (intento V2)..."
# Usamos el script que ya creamos, ahora que el objetivo existe
./fix_worker_sidecar_v2.sh

EOF

chmod +x recover_stack.sh
./recover_stack.sh
