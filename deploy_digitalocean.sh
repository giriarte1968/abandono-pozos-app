cat > deploy_digitalocean.sh << 'EOF'
#!/bin/bash

# ==============================================================================
# deploy_digitalocean.sh
# Script de inicialización y despliegue para DigitalOcean Droplet (Ubuntu/Debian)
# ==============================================================================

set -e

echo ">>> 1. Preparando entorno (Docker & Security)..."

# Actualizar sistema
sudo apt-get update && sudo apt-get install -y ca-certificates curl gnupg

# Instalar Docker (si no existe)
if ! command -v docker &> /dev/null; then
    echo "Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "⚠️ Docker instalado. Es posible que necesites cerrar sesión y volver a entrar para usar 'docker' sin sudo."
else
    echo "✅ Docker ya está instalado."
fi

# Configurar Firewall (UFW)
# Permitimos SSH (22), HTTP (80) y Temporal UI (8080)
# Bloqueamos MySQL (3306) externamente por seguridad
echo "Configurando Firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 8080/tcp
sudo ufw --force enable
echo "✅ Firewall configurado. MySQL protegido."


echo ">>> 2. Configurando Variables de Entorno..."
if [ ! -f .env ]; then
    echo "Creando archivo .env..."
    cat > .env << 'ENV'
# Database
MYSQL_ROOT_PASSWORD=pna_root_prod_secure
MYSQL_DATABASE=pna_system
MYSQL_USER=pna_user
MYSQL_PASSWORD=pna_pass_prod_secure
VISIBILITY_DB=pna_system_visibility

# Application
STREAMLIT_SERVER_PORT=8501
TEMPORAL_HOST=temporal
TEMPORAL_PORT=7233
ENV
    echo "✅ .env creado con valores por defecto (¡CAMBIAR EN PRODUCCIÓN!)."
else
    echo "ℹ️ Archivo .env ya existe, usándolo."
fi


echo ">>> 3. Generando Configuración Dinámica de Temporal..."
mkdir -p config/dynamicconfig
if [ ! -f config/dynamicconfig/production.yaml ]; then
    cat > config/dynamicconfig/production.yaml << 'YAML'
# Configuración vacía para usar defaults en producción
# Aquí se pueden agregar rate limits o reglas específicas
YAML
fi


echo ">>> 4. Desplegando Stack en Docker Swarm (o Compose)..."
# Usamos 'docker compose' (v2) estándar
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

echo ">>> 5. Esperando servicios..."
sleep 10
if docker compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "✅✅ DESPLIEGUE EXITOSO ✅✅"
    echo ""
    echo "Accede a la aplicación en: http://$(curl -s ifconfig.me)"
    echo "Accede a Temporal UI en:   http://$(curl -s ifconfig.me):8080"
else
    echo "❌ Algo falló. Revisa logs con: docker compose -f docker-compose.prod.yml logs"
fi
EOF

chmod +x deploy_digitalocean.sh
