# 🚀 Deploy en DigitalOcean App Platform

Guía paso a paso para desplegar AbandonPro en DigitalOcean App Platform.

## 📋 Prerrequisitos

1. **Cuenta en DigitalOcean**: https://cloud.digitalocean.com/
2. **GitHub/GitLab**: Repositorio con tu código
3. **Tarjeta de crédito**: Para activar la cuenta (DO da $200 de crédito inicial)

## 🔧 Configuración Pre-Deploy

### 1. Verificar Archivos Necesarios

Asegúrate de tener estos archivos en tu repo:

```
├── Dockerfile                 ✅ (Ya creado)
├── requirements.txt           ✅ (Ya actualizado)
├── .dockerignore             ✅ (Ya creado)
├── .do/
│   └── app.yaml              ✅ (Ya creado)
└── frontend/
    └── app.py                ✅ (Tu app)
```

### 2. Configurar Variables de Entorno (Secretos)

En DigitalOcean vas a configurar:

```bash
GEMINI_API_KEY=tu_api_key_de_google_aqui
```

**Nota**: Si no tienes API Key, la app funciona igual en modo offline con el motor de reglas.

## 🚀 Pasos para Deploy

### Opción A: Deploy Automático desde GitHub (Recomendado)

1. **Subir código a GitHub**
   ```bash
   git add .
   git commit -m "feat: Configuración para DigitalOcean App Platform"
   git push origin main
   ```

2. **En DigitalOcean Console**:
   - Ve a https://cloud.digitalocean.com/apps
   - Click "Create App"
   - Selecciona "GitHub" como fuente
   - Autoriza DigitalOcean a acceder a tu repo
   - Selecciona el repositorio de AbandonPro

3. **Configurar la App**:
   - **Branch**: main (o la que uses)
   - **Source Directory**: / (raíz)
   - DigitalOcean detectará automáticamente el Dockerfile

4. **Configurar Variables de Entorno**:
   - Ve a "Settings" → "App-Level Environment Variables"
   - Agrega: `GEMINI_API_KEY` (como secreto)

5. **Elegir Plan**:
   - **Basic**: $10/mes (1GB RAM, 1 CPU) - **Mínimo recomendado** para Streamlit + AI
   - **Professional**: $12/mes (1GB RAM, 1 CPU) - Con soporte para backup y más recursos

6. **Deploy**:
   - Click "Create Resources"
   - Espera 3-5 minutos
   - ¡Listo! DigitalOcean te dará una URL tipo: `https://abandono-pozos-app-xxx.ondigitalocean.app`

### Opción B: Deploy con doctl (CLI)

1. **Instalar doctl**:
   ```bash
   # Windows (con chocolatey)
   choco install doctl
   
   # O descargar desde:
   # https://docs.digitalocean.com/reference/doctl/how-to/install/
   ```

2. **Autenticar**:
   ```bash
   doctl auth init
   # Ingresa tu token de DigitalOcean
   ```

3. **Crear App**:
   ```bash
   doctl apps create --spec .do/app.yaml
   ```

## 💰 Costos Estimados

| Recurso | Costo Mensual |
|---------|---------------|
| Basic-S (1GB RAM) | $10 USD |
| Professional (1GB RAM) | $12 USD |
| Professional (2GB RAM) | $24 USD |
| Dominio personalizado | $0-12 USD/año |

**Total mínimo**: $10-12 USD/mes

## 🔧 Configuración Post-Deploy

### 1. Configurar Dominio Personalizado (Opcional)

En DigitalOcean Console:
1. Ve a tu App → "Settings" → "Domains"
2. Click "Add Domain"
3. Ingresa tu dominio (ej: abandonpro.tudominio.com)
4. Seguir instrucciones de DNS

### 2. Configurar CI/CD Automático

DigitalOcean App Platform hace deploy automático cada vez que haces push a main:

```bash
# Hacer cambios locales
# ...

# Subir a GitHub
git add .
git commit -m "fix: Corrección de bug en dashboard"
git push origin main

# DigitalOcean detecta automáticamente y redeploya en ~2 minutos
```

### 3. Monitorear Logs

En DigitalOcean Console:
- Ve a tu App → "Runtime Logs"
- O usa CLI:
  ```bash
  doctl apps logs <app-id>
  ```

## 🧪 Testing Post-Deploy

Una vez desplegado, verifica:

1. **Acceso a la app**:
   - Abre la URL proporcionada por DigitalOcean
   - Deberías ver el login de AbandonPro

2. **Login**:
   - Usuario: Cualquiera (está en modo mock)
   - Rol: "Gerente" para acceso completo

3. **Módulos**:
   - ✅ Dashboard Operativo
   - ✅ Dashboard Financiero
   - ✅ Chat AI (funciona en modo offline)

## 🔒 Seguridad

### Habilitar HTTPS
- DigitalOcean App Platform incluye HTTPS automático (Let's Encrypt)
- Redirección HTTP → HTTPS incluida

### Variables Sensibles
- Nunca commitees el archivo `.env`
- Usa los "App-Level Environment Variables" de DigitalOcean
- Las variables marcadas como SECRET están encriptadas

## 🐛 Troubleshooting

### Error: "Build Failed"
```bash
# Verificar Dockerfile localmente
docker build -t abandonpro:test .
docker run -p 8501:8501 abandonpro:test
```

### Error: "App unhealthy"
- Verificar que `frontend/app.py` existe
- Verificar que el puerto 8501 está expuesto
- La app tiene un healthcheck cada 30s con un timeout de 5s. Verifica los logs si falla.

### Error: "Module not found"
- Asegúrate de que todas las dependencias están en `requirements.txt`
- Prueba localmente:
  ```bash
  pip install -r requirements.txt
  streamlit run frontend/app.py
  ```

## 📝 Checklist Pre-Deploy

- [ ] Dockerfile creado y probado localmente
- [ ] requirements.txt con todas las dependencias
- [ ] .dockerignore configurado
- [ ] Código subido a GitHub
- [ ] Variables de entorno configuradas en DO
- [ ] API Key de Gemini (opcional)
- [ ] Dominio configurado (opcional)

## 🎯 Siguientes Pasos

1. Hacer deploy inicial
2. Configurar dominio personalizado
3. Agregar usuarios de prueba
4. Configurar monitoreo (opcional)

## 📞 Soporte

- **DigitalOcean Docs**: https://docs.digitalocean.com/products/app-platform/
- **Community**: https://www.digitalocean.com/community
- **Status Page**: https://status.digitalocean.com/

---

**Nota**: La primera vez puede tardar ~5 minutos en el build inicial. Los deploys siguientes toman ~2 minutos.
