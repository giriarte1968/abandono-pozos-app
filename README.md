# Abandono Pozos App - Sistema de Gestión de Abandono de Pozos (P&A)

Sistema integral para la gestión de operaciones de Plug & Abandonment (P&A) en la industria petrolera, con módulos operativos, financieros y de control contractual.

## 🚀 Quick Start - Desarrollo Local

### Ejecutar Frontend (Streamlit)

```bash
cd C:\Users\Gustavo\.gemini\antigravity\scratch
streamlit run frontend/app.py
```

La aplicación estará disponible en: http://localhost:8501

### Módulos Disponibles

- **Operaciones**: Proyectos, Logística, Cementación, Cierre Técnico
- **Finanzas**: Dashboard Financiero, Contratos, Certificaciones
- **Control & Calidad**: Cumplimiento, Auditoría, Documentación
- **Administración**: Datos Maestros (Operativos + Financieros)

## 💰 Módulo Financiero & Control Contractual

### Características Principales

#### 📊 Dashboard Financiero
- **KPIs en tiempo real**: Backlog, avance físico/financiero, saldo de caja, días de cobertura
- **Proyección de flujo de fondos**: 12 meses con gráficos interactivos
- **Alertas automáticas**: Cobertura < 45 días, backlog bajo

#### 📋 Gestión de Contratos
- Creación y administración de contratos con clientes (SureOil, YPF, Petrobras)
- Cálculo automático de montos y backlog
- Asignación de pozos a contratos
- Validación de reglas de negocio (no edición con certificaciones)

#### ✅ Certificaciones de Obra
- **Integración con operaciones**: Solo pozos COMPLETADOS pueden certificarse
- **Generación automática de facturas**: Con plazos de pago configurables
- **Cálculo de rentabilidad**: Ingresos vs costos operativos
- **Sincronización bidireccional**: Estado de pozos entre operaciones y finanzas

#### 💡 Asistente AI (Mistral/Gemini)
El asistente virtual ofrece:
- **Análisis de situación dual**: Operativo + Financiero
- **Recomendaciones inteligentes**: Basadas en datos reales
- **Expert System Prompt**: Rol de Ingeniero Petróleo Senior especializado en P&A.
- **Cascada de Modelos**: Mistral (principal) → Gemini (fallback) → Offline (motor de reglas).
- **Reducción de latencia**: Optimizado para respuestas rápidas.

### Datos de Ejemplo (Mock)

El sistema incluye datos de prueba realistas:

**Contratos:**
- SureOil - Lote Norte: $740,000 (4 pozos)
- YPF - Abandono Integral: $585,000 (3 pozos)
- Petrobras - Mantenimiento: $525,000 (3 pozos)

**Pozos integrados (10):**
- X-123, A-321, Z-789, M-555 (SureOil)
- P-001, P-002, H-101 (YPF)
- H-102, T-201, C-301 (Petrobras)

**Estado financiero inicial:**
- Backlog total: $1,470,000
- Avance: 30.5%
- Caja: $140,000
- Cobertura: 42 días (⚠️ alerta)

## 🏗️ Arquitectura de Integración

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Streamlit)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │Dashboard │ │Contratos │ │Certificac│ │Datos     │   │
│  │Financiero│ │          │ │  iones   │ │Maestros  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌────────────────┐  ┌─────────────────┐
│   MockApi    │  │  Financial     │  │   AI Service    │
│   Client     │  │  Service Mock  │  │   (Gemini)      │
│(Operaciones) │  │   (Finanzas)   │  │   + Reglas      │
└──────────────┘  └────────────────┘  └─────────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────┴──────┐
                    │ persistence │
                    │  _db.json   │
                    └─────────────┘
```

### Flujo de Integración Operaciones ↔ Finanzas

1. **Pozo completado** en operaciones → Disponible para certificación en finanzas
2. **Certificación** en finanzas → Actualiza backlog y genera factura
3. **Costos operativos** → Integrados en análisis de rentabilidad
4. **Estado financiero** → Disponible en chat y dashboards

## 🧪 Testing

```bash
# Ejecutar validación del módulo financiero
python test_financial_mock_validation.py

# Probar chat en modo offline
python test_chat_offline.py
```

## 🗄️ Estructura de Base de Datos

### Módulo Financiero (SQL)

Ver `db/migrations/007_financial_module.sql`:

- **CONTRATOS**: Información contractual y montos
- **CERTIFICACIONES**: Obras certificadas y avances
- **FACTURAS**: Documentos de cobro generados
- **COBRANZAS**: Pagos recibidos
- **COSTOS_REALES**: Gastos operativos integrados
- **FLUJO_FONDOS**: Proyecciones financieras
- **PARAMETROS_MACRO**: Variables económicas

## 🔧 Configuración

### Variables de Entorno

Crear archivo `.env`:

```
GEMINI_API_KEY=tu_api_key_aqui
```

> **Nota**: Si no se configura API Key (Gemini/OpenRouter), el sistema funciona en modo offline con motor de reglas.

### Roles de Usuario
El sistema utiliza un login simplificado (sin contraseña) para facilitar las pruebas:
- **admin**: Acceso total operativo y financiero
- **sebastian.cannes**: Gerente / Proyecto
- **juan.supervisor**: Supervisor de Campo
- **demo.user**: Perfil HSE / Calidad

## ☁️ Infraestructura & Despliegue

### Producción (DigitalOcean)
La app está configurada para DigitalOcean App Platform con optimizaciones:
- **RAM**: 1GB (Basic-S) para mejor rendimiento de Streamlit.
- **Healthchecks**: Monitoreo activo cada 30s.
- **Optimización**: Imágenes WebP y cacheo global de assets.

### Local (Docker)
Inicia el stack completo incluyendo Temporal y MySQL:

```powershell
# Iniciar stack
docker compose up -d
```

### Servicios

- **MySQL**: localhost:3306
- **Temporal Server**: localhost:7233
- **Temporal UI**: http://localhost:8080
- **Streamlit**: http://localhost:8501

## 📚 Documentación Adicional

- **DOCKER_SETUP.md**: Guía completa de instalación local
- **DEPLOY_DIGITALOCEAN.md**: Guía de despliegue en la nube
- **force_restore_temporal_v2.sh**: Recuperación de estado de Temporal
- **deep_verify.sh**: Script de validación integral del sistema

## 🎯 Roadmap

- [x] Módulo Financiero con dashboard y KPIs
- [x] Integración Operaciones ↔ Finanzas
- [x] Chat AI con análisis dual (operativo + financiero)
- [x] Sistema de recomendaciones automáticas
- [x] Optimización de assets (WebP) y performance
- [ ] Integración con sistemas externos (SAP, Bancos)
- [ ] Reportes automatizados por email

## 👥 Equipo

Desarrollado por giriarte1968.

---

**Versión**: 2.2.0 | **Estado**: Dev/Mock Mode | **Última actualización**: 2026-02-19
