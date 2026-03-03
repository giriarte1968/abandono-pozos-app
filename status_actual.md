# Estado Actual del Sistema P&A - Resumen de Modelado

Este documento resume el estado actual del modelado de datos, procesos operativos y estructura financiera del sistema de Abandono de Pozos (P&A).

## 1. Modelo Actual de Entidades

El sistema utiliza una arquitectura que separa **Datos Maestros (Catálogos)**, **Datos Operativos (Transaccionales/Estado)** y **Módulo Financiero**.

### Datos Maestros (Catálogos Estáticos/Lento Crecimiento)
- **Pozos (`tbl_pozos` / `WELL`)**: Entidad central que representa el activo físico. Contiene atributos como nombre, yacimiento, coordenadas geográficas, profundidad total y estado actual (`ACTIVO`, `INACTIVO`, `ABANDONADO`).
- **Campañas (`tbl_campanas`)**: Agrupación lógica de proyectos de abandono por temporada o región geográfica. Incluye fechas previstas, estados de la campaña y responsables.
- **Personal (`tbl_personal_catalogo`)**: Registro centralizado de recursos humanos. Incluye DNI, nombre, rol principal (`Supervisor`, `HSE`, `Operador`) y banderas de criticidad.
- **Equipos (`tbl_equipos_catalogo`)**: Catálogo de activos físicos operativos como unidades de `Pulling`, `Cementadores` o `Cisternas`. Rastrea número de serie, marca, modelo y estado de operatividad.
- **Insumos (`supplies` en Mock/Persistence)**: Catálogo de materiales necesarios (cemento, agua, gasoil) con niveles de stock mínimo.
- **Jurisdicciones y Regulaciones (`tbl_jurisdiccion`, `tbl_version_regulacion`)**: Estructura para manejar normativas legales por región (Nacional, Provincial).

### Datos Operativos (Flujo y Cumplimiento)
- **Expedientes de Abandono (`tbl_expedientes_abandono`)**: Vincula un Pozo con una Campaña y un flujo de trabajo orquestado. Es el "corazón" operativo.
- **Partes Diarios (`tbl_partes_diarios`)**: Reportes transaccionales de campo que capturan el progreso diario, consumo de stock, personal presente y condiciones climáticas.
- **Validaciones y Cumplimiento (`tbl_validaciones_personal`, `tbl_resultado_cumplimiento`)**: Registro de chequeos automáticos y manuales (Médico, Inducciones, Reglas de Ingeniería).
- **Evidencia Digital (`well_evidence`)**: Registro persistente de archivos, fotos y documentos técnicos asociados a etapas específicas del pozo.
- **Auditoría e Inmutabilidad (`audit_events`)**: Trail de eventos con hashing encadenado ("Blockchain Light") para garantizar la trazabilidad defensible de cada cambio de estado.

## 2. Modelado del Expediente de Pozo

El **Expediente de Pozo** no es solo un registro estático, sino un **hub de estado dinámico** vinculado a un motor de orquestación (Temporal.io).

- **Persistencia**: Se almacena en `tbl_expedientes_abandono`.
- **Atributos Clave**:
    - `id_pozo`: Referencia al activo físico.
    - `id_workflow_temporal`: ID del workflow activo que orquesta la lógica de negocio.
    - `progreso_pct`: Porcentaje de avance físico calculado.
    - `estado_expediente`: Ciclo de vida (desde `INICIO_TRAMITE` hasta `FINALIZADO`).
    - `estado_cierre`: Clasificación de la calidad del abandono (`EN_PROCESO`, `APROBADO`, `CERRADO_DEFENDIBLE`).
- **Relaciones**: Es el nodo central que conecta el pozo con sus partes diarios, evidencias, personal asignado y costos reales.

## 3. Manejo de Etapas

El concepto de "Etapa" se maneja en tres dimensiones complementarias:

1.  **Ciclo de Vida de Negocio (Hitos)**: Definido por los estados del expediente:
    - *Inicio Trámite / Planificación*
    - *Logística / Movilización*
    - *Ejecución Campo (Cementación / Tapones)*
    - *Cierre Técnico y Auditoría*
2.  **Contexto Operativo del Chat/IA**: Atributo `contexto_etapa` en el chat operativo para que el asistente AI entienda si se está hablando de cementación, logística o legal.
3.  **Desglose de Costos**: Utilizado en `COSTOS_REALES` (`ETAPA`) para imputar gastos a fases específicas (ej. DTM - Desmontaje/Traslado/Montaje).

## 4. Concepto de Contrato

**Sí, existe el concepto de contrato como entidad formal.**

- **Entidad `CONTRATOS`**: Maneja la relación comercial con los clientes (ej. SureOil, YPF, Petrobras).
- **Atributos Financieros**: Almacena el `MONTO_TOTAL_CONTRACTUAL`, el `VALOR_UNITARIO_BASE_USD` por pozo y rastrea el `BACKLOG_RESTANTE`.
- **Integración**: Los pozos se asocian a contratos para habilitar la **Certificación de Obra**. Un pozo completado en la dimensión operativa habilita un hito de certificación en la dimensión financiera.

## 5. Recurso como Entidad Persistente

**Sí, los recursos son entidades persistentes y catalalizadas.**

- No se manejan como simples strings en los partes diarios, sino como referencias a **`tbl_personal_catalogo`** y **`tbl_equipos_catalogo`**.
- Esto permite:
    - Mantener un historial de validaciones HSE (médicos, inducciones) por persona.
    - Rastrear el estado de mantenimiento y disponibilidad por equipo.
    - Gestionar la asignación dinámica de recursos críticos a expedientes específicos.

## 6. El Tiempo: ¿Atributo o Eje Estructural?

El sistema maneja el tiempo de dos formas distintas según el módulo:

- **Como Atributo (Operaciones)**: En las tablas operativas (`tbl_expedientes_abandono`, `tbl_partes_diarios`), el tiempo se registra como atributos de marca temporal (`fecha_inicio`, `ts_evento`, `fecha_operativa`) para fines de trazabilidad y auditoría.
- **Como Eje Estructural (Finanzas)**: En el módulo financiero y gerencial, el tiempo se convierte en un eje estructural de análisis.
    - La tabla **`FLUJO_FONDOS`** utiliza el `PERIODO` (mes/año) como clave primaria estructural para proyecciones a 12 meses.
    - Los Dashboards utilizan el tiempo como eje X para visualizar la proyección de caja, cobertura y avance de backlog.

---
**Generado por**: Antigravity AI
**Fecha**: 2026-03-02
**Ubicación**: `scratch/status_actual.md`
