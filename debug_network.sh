cat > debug_network.sh << 'EOF'
#!/bin/bash
echo "🔍 1. Listando todas las redes Podman..."
podman network ls

echo ""
echo "🔍 2. Inspeccionando la red del contenedor Temporal..."
# Muestra el JSON de la configuración de red de Temporal
podman inspect braco_temporal_1 --format '{{json .NetworkSettings.Networks}}'

echo ""
echo "🔍 3. Buscando nombre de red específico..."
# Intenta extraer el nombre de la llave del mapa de redes
podman inspect braco_temporal_1 --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}'

echo ""
echo "🔍 4. Verificando si existe un Pod agrupador..."
podman pod ps
EOF

chmod +x debug_network.sh
./debug_network.sh
