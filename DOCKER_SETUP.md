# Docker Setup Guide (Windows)

## 🔧 Pasos de Instalación

### Paso 1: Instalar Docker Desktop

1. Descarga Docker Desktop desde: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Ejecuta el instalador.
3. Asegúrate de que la opción **"Use the WSL 2 based engine"** esté seleccionada durante la instalación.

### Paso 2: Reiniciar tu computadora (si se solicita)

### Paso 3: Iniciar Docker Desktop

1. Abre la aplicación de Docker Desktop.
2. Acepta los términos de servicio.
3. Espera a que el icono de la ballena en la barra de tareas esté estable (indicando que el motor de Docker está funcionando).

### Paso 4: Iniciar el Stack de P&A

Abre una terminal (PowerShell o CMD) y navega al proyecto:

```powershell
cd C:\Users\Gustavo\.gemini\antigravity\scratch

# Iniciar todos los servicios (MySQL + Temporal + Worker + Frontend)
docker compose up -d
```

### Paso 5: Verificar

Espera unos 15-30 segundos para que MySQL y Temporal se inicialicen completamente y luego abre:
- **Frontend**: [http://localhost:8501](http://localhost:8501)
- **Temporal UI**: [http://localhost:8080](http://localhost:8080)

---

## 📋 Referencia Rápida de Comandos

```powershell
# Iniciar servicios en segundo plano
docker compose up -d

# Detener servicios
docker compose down

# Ver logs en tiempo real
docker compose logs -f

# Ver estado de los contenedores
docker compose ps

# Reiniciar servicios
docker compose restart
```

---

## 🐛 Resolución de Problemas

### "Docker Desktop is not running"
- Asegúrate de haber iniciado la aplicación de Docker Desktop.
- Verifica que el servicio de Docker esté en ejecución.

### "Permission denied"
- En Windows, generalmente no necesitas permisos de administrador para ejecutar comandos de Docker si tu usuario está en el grupo `docker-users` (configurado automáticamente por el instalador).

### "Port already in use"
- Asegúrate de que no tengas otros servicios ocupando los puertos 3306, 7233, 8080 u 8501.
