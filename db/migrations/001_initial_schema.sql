-- P&A System - Initial Schema Migration
-- Based on ETAPA A (data_model.md)

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS pna_system;
USE pna_system;

-- ============================================
-- MASTER DATA TABLES
-- ============================================

-- Pozos
CREATE TABLE IF NOT EXISTS tbl_pozos (
    id_pozo VARCHAR(50) PRIMARY KEY,
    nombre_pozo VARCHAR(200) NOT NULL,
    id_yacimiento VARCHAR(50) NOT NULL,
    lat DECIMAL(10, 7) NOT NULL,
    lon DECIMAL(10, 7) NOT NULL,
    estado_pozo VARCHAR(50) NOT NULL,
    profundidad_total DECIMAL(10, 2),
    fecha_perforacion DATE,
    
    creado_por VARCHAR(100) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_por VARCHAR(100),
    actualizado_en TIMESTAMP,
    
    CONSTRAINT chk_estado_pozo CHECK (estado_pozo IN ('ACTIVO', 'INACTIVO', 'ABANDONADO'))
);

CREATE INDEX idx_pozos_yacimiento ON tbl_pozos(id_yacimiento);
CREATE INDEX idx_pozos_estado ON tbl_pozos(estado_pozo);

-- Campañas
CREATE TABLE IF NOT EXISTS tbl_campanas (
    id_campana VARCHAR(50) PRIMARY KEY,
    nombre_campana VARCHAR(200) NOT NULL,
    descripcion TEXT,
    fecha_inicio DATE NOT NULL,
    fecha_fin_prevista DATE,
    fecha_fin_real DATE,
    estado_campana VARCHAR(50) NOT NULL,
    id_responsable VARCHAR(100),
    
    creado_por VARCHAR(100) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_estado_campana CHECK (estado_campana IN ('PLANIFICADA', 'EN_CURSO', 'FINALIZADA', 'CANCELADA')),
    CONSTRAINT chk_fechas_campana CHECK (fecha_fin_prevista >= fecha_inicio)
);

-- Personal Catálogo
CREATE TABLE IF NOT EXISTS tbl_personal_catalogo (
    id_persona VARCHAR(50) PRIMARY KEY,
    dni VARCHAR(20) UNIQUE NOT NULL,
    nombre_completo VARCHAR(200) NOT NULL,
    rol_principal VARCHAR(100) NOT NULL,
    es_recurso_critico BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    
    creado_por VARCHAR(100) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_personal_rol ON tbl_personal_catalogo(rol_principal);

-- Equipos Catálogo
CREATE TABLE IF NOT EXISTS tbl_equipos_catalogo (
    id_equipo VARCHAR(50) PRIMARY KEY,
    nombre_equipo VARCHAR(200) NOT NULL,
    tipo_equipo VARCHAR(100) NOT NULL,
    marca VARCHAR(100),
    modelo VARCHAR(100),
    numero_serie VARCHAR(100) UNIQUE,
    es_critico BOOLEAN DEFAULT FALSE,
    
    activo BOOLEAN DEFAULT TRUE,
    creado_por VARCHAR(100) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_equipos_tipo ON tbl_equipos_catalogo(tipo_equipo);

-- ============================================
-- OPERATIONAL DATA TABLES
-- ============================================

-- Expedientes
CREATE TABLE IF NOT EXISTS tbl_expedientes_abandono (
    id_expediente VARCHAR(50) PRIMARY KEY,
    id_pozo VARCHAR(50) NOT NULL,
    id_campana VARCHAR(50) NOT NULL,
    id_workflow_temporal VARCHAR(100) UNIQUE,
    
    estado_expediente VARCHAR(50) NOT NULL,
    fecha_inicio_tramite DATE NOT NULL,
    fecha_inicio_ejecucion DATE,
    fecha_finalizacion DATE,
    
    progreso_pct DECIMAL(5, 2) DEFAULT 0.00,
    proximo_hito VARCHAR(200),
    
    responsable_tecnico VARCHAR(100) NOT NULL,
    responsable_campo VARCHAR(100),
    
    creado_por VARCHAR(100) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_por VARCHAR(100),
    actualizado_en TIMESTAMP,
    
    FOREIGN KEY (id_pozo) REFERENCES tbl_pozos(id_pozo),
    FOREIGN KEY (id_campana) REFERENCES tbl_campanas(id_campana),
    CONSTRAINT chk_estado_expediente CHECK (estado_expediente IN (
        'INICIO_TRAMITE', 'PLANIFICACION_LOGISTICA', 'EJECUCION_CAMPO',
        'BLOCKED_BY_INCIDENT', 'CIERRE_Y_AUDITORIA', 'FINALIZADO'
    )),
    CONSTRAINT chk_progreso CHECK (progreso_pct BETWEEN 0 AND 100)
);

CREATE INDEX idx_expedientes_pozo ON tbl_expedientes_abandono(id_pozo);
CREATE INDEX idx_expedientes_estado ON tbl_expedientes_abandono(estado_expediente);

-- Partes Diarios
CREATE TABLE IF NOT EXISTS tbl_partes_diarios (
    id_parte_diario VARCHAR(50) PRIMARY KEY,
    id_expediente VARCHAR(50) NOT NULL,
    fecha_operativa DATE NOT NULL,
    turno VARCHAR(20) NOT NULL,
    
    habilitado_operar BOOLEAN NOT NULL DEFAULT FALSE,
    estado_agregado VARCHAR(50) NOT NULL,
    razones_bloqueo JSON,
    
    contenido_operativo JSON NOT NULL,
    
    personal_ok BOOLEAN NOT NULL DEFAULT FALSE,
    equipos_ok BOOLEAN NOT NULL DEFAULT FALSE,
    logistica_ok BOOLEAN NOT NULL DEFAULT FALSE,
    stock_ok BOOLEAN NOT NULL DEFAULT TRUE,
    permisos_ok BOOLEAN NOT NULL DEFAULT FALSE,
    meteorologia_apto BOOLEAN NOT NULL DEFAULT TRUE,
    
    destinatario_principal VARCHAR(100),
    requiere_revision BOOLEAN DEFAULT FALSE,
    revisado_por VARCHAR(100),
    revisado_en TIMESTAMP,
    
    reportado_por VARCHAR(100) NOT NULL,
    reportado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aprobado_por VARCHAR(100),
    aprobado_en TIMESTAMP,
    
    FOREIGN KEY (id_expediente) REFERENCES tbl_expedientes_abandono(id_expediente),
    CONSTRAINT chk_turno CHECK (turno IN ('MANANA', 'TARDE', 'NOCHE', 'COMPLETO')),
    CONSTRAINT chk_estado_agregado CHECK (estado_agregado IN ('HABILITADO', 'BLOQUEADO', 'PARCIAL')),
    CONSTRAINT uq_parte_fecha_turno UNIQUE (id_expediente, fecha_operativa, turno)
);

CREATE INDEX idx_partes_expediente ON tbl_partes_diarios(id_expediente);
CREATE INDEX idx_partes_fecha ON tbl_partes_diarios(fecha_operativa);

-- Asignaciones Personal
CREATE TABLE IF NOT EXISTS tbl_asignaciones_personal (
    id_asignacion VARCHAR(50) PRIMARY KEY,
    id_expediente VARCHAR(50) NOT NULL,
    id_persona VARCHAR(50) NOT NULL,
    rol_en_expediente VARCHAR(100) NOT NULL,
    es_critico_operacion BOOLEAN NOT NULL DEFAULT FALSE,
    
    fecha_asignacion DATE NOT NULL,
    fecha_desasignacion DATE,
    motivo_desasignacion VARCHAR(500),
    
    asignado_por VARCHAR(100) NOT NULL,
    asignado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (id_expediente) REFERENCES tbl_expedientes_abandono(id_expediente),
    FOREIGN KEY (id_persona) REFERENCES tbl_personal_catalogo(id_persona)
);

CREATE INDEX idx_asignaciones_expediente ON tbl_asignaciones_personal(id_expediente);

-- Validaciones Personal
CREATE TABLE IF NOT EXISTS tbl_validaciones_personal (
    id_validacion VARCHAR(50) PRIMARY KEY,
    id_expediente VARCHAR(50) NOT NULL,
    id_persona VARCHAR(50) NOT NULL,
    tipo_validacion VARCHAR(50) NOT NULL,
    
    estado_validacion BOOLEAN NOT NULL,
    fecha_vigencia_desde DATE NOT NULL,
    fecha_vigencia_hasta DATE NOT NULL,
    
    fuente VARCHAR(20) NOT NULL,
    sistema_origen VARCHAR(100),
    
    validado_por VARCHAR(100) NOT NULL,
    validado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    justificacion TEXT,
    
    version INT DEFAULT 1,
    
    FOREIGN KEY (id_expediente) REFERENCES tbl_expedientes_abandono(id_expediente),
    FOREIGN KEY (id_persona) REFERENCES tbl_personal_catalogo(id_persona),
    CONSTRAINT chk_tipo_validacion CHECK (tipo_validacion IN ('MEDICAL', 'INDUCTION', 'CERTIFICATION')),
    CONSTRAINT chk_fuente_validacion CHECK (fuente IN ('AUTOMATIC', 'EXTERNAL', 'MANUAL')),
    CONSTRAINT chk_vigencia CHECK (fecha_vigencia_hasta >= fecha_vigencia_desde),
    CONSTRAINT chk_justificacion_manual CHECK (
        (fuente = 'MANUAL' AND justificacion IS NOT NULL) OR 
        (fuente != 'MANUAL')
    )
);

CREATE INDEX idx_validaciones_expediente ON tbl_validaciones_personal(id_expediente);
CREATE INDEX idx_validaciones_persona ON tbl_validaciones_personal(id_persona);

-- ============================================
-- AUDIT AND HISTORY TABLES
-- ============================================

-- Eventos de Auditoría
CREATE TABLE IF NOT EXISTS tbl_eventos_auditoria (
    id_evento VARCHAR(50) PRIMARY KEY,
    id_expediente VARCHAR(50),
    tipo_evento VARCHAR(100) NOT NULL,
    
    payload JSON NOT NULL,
    
    usuario VARCHAR(100) NOT NULL,
    rol_usuario VARCHAR(100),
    ip_origen VARCHAR(50),
    
    ts_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    FOREIGN KEY (id_expediente) REFERENCES tbl_expedientes_abandono(id_expediente)
);

CREATE INDEX idx_eventos_expediente ON tbl_eventos_auditoria(id_expediente);
CREATE INDEX idx_eventos_tipo ON tbl_eventos_auditoria(tipo_evento);
CREATE INDEX idx_eventos_timestamp ON tbl_eventos_auditoria(ts_evento);

-- Overrides Manuales
CREATE TABLE IF NOT EXISTS tbl_overrides_manuales (
    id_override VARCHAR(50) PRIMARY KEY,
    id_expediente VARCHAR(50) NOT NULL,
    dominio VARCHAR(50) NOT NULL,
    id_objeto VARCHAR(50) NOT NULL,
    campo_overrideado VARCHAR(100) NOT NULL,
    
    valor_automatico JSON,
    valor_manual JSON NOT NULL,
    
    responsable VARCHAR(100) NOT NULL,
    justificacion TEXT NOT NULL,
    aprobado_por VARCHAR(100),
    
    fecha_override DATE NOT NULL,
    valido_hasta DATE,
    
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (id_expediente) REFERENCES tbl_expedientes_abandono(id_expediente),
    CONSTRAINT chk_dominio_override CHECK (dominio IN ('PERSONAL', 'EQUIPO', 'PERMISO', 'OTRO'))
);

CREATE INDEX idx_overrides_expediente ON tbl_overrides_manuales(id_expediente);

-- Chat Operativo
CREATE TABLE IF NOT EXISTS tbl_chat_operativo (
    id_mensaje VARCHAR(50) PRIMARY KEY,
    id_expediente VARCHAR(50) NOT NULL,
    id_pozo VARCHAR(50),
    usuario VARCHAR(100) NOT NULL,
    rol VARCHAR(50) NOT NULL,
    origen ENUM('HUMANO', 'IA') NOT NULL,
    mensaje TEXT NOT NULL,
    contexto_etapa VARCHAR(50) NOT NULL,
    ts_mensaje TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (id_expediente) REFERENCES tbl_expedientes_abandono(id_expediente)
);

CREATE INDEX idx_chat_expediente ON tbl_chat_operativo(id_expediente);
CREATE INDEX idx_chat_ts ON tbl_chat_operativo(ts_mensaje);

-- Success message
SELECT 'Database schema created successfully' AS status;
