-- Migration: 003_audit_and_evidence.sql
-- Goal: Advanced Regulatory Audit & Evidence Management
-- Principles: Immutable, Event-Driven, Verifiable

-- 1. Audit Events Table (Blockchain Light)
CREATE TABLE IF NOT EXISTS audit_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_usuario VARCHAR(50) NOT NULL,
    rol_usuario VARCHAR(50) NOT NULL,
    tipo_evento VARCHAR(100) NOT NULL, -- WORKFLOW_STEP, SIGNAL, OVERRIDE, EVIDENCE, DATA_CHANGE
    entidad VARCHAR(50) NOT NULL,     -- POZO, EQUIPO, CAMPANA, USUARIO
    entidad_id VARCHAR(50) NOT NULL,
    estado_anterior JSON,
    estado_nuevo JSON,
    metadata JSON,                    -- Extra context: IP, User Agent, etc.
    ip_origen VARCHAR(45),
    hash_previo VARCHAR(64),          -- Reference to the previous event's hash
    hash_evento VARCHAR(64) NOT NULL, -- SHA256(ALL FIELDS + HASH_PREVIO)
    INDEX idx_entidad (entidad, entidad_id),
    INDEX idx_tipo (tipo_evento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Evidence Registry Table
CREATE TABLE IF NOT EXISTS well_evidence (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_pozo VARCHAR(50) NOT NULL,
    etapa_workflow VARCHAR(50) NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    path_archivo VARCHAR(512) NOT NULL,
    mime_type VARCHAR(100),
    tamano_bytes BIGINT,
    hash_sha256 VARCHAR(64) NOT NULL,
    id_usuario_carga VARCHAR(50),
    timestamp_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON, -- Lat/Lon if GPS, Duration if Video
    INDEX idx_pozo_etapa (id_pozo, etapa_workflow)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Operational Overrides Table
CREATE TABLE IF NOT EXISTS operational_overrides (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_pozo VARCHAR(50) NOT NULL,
    gate_id VARCHAR(50) NOT NULL, -- DTM, PERS, HSE, WEATHER
    id_usuario_autoriza VARCHAR(50) NOT NULL,
    motivo_obligatorio TEXT NOT NULL,
    valido_hasta TIMESTAMP NULL,
    timestamp_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_evento_auditoria INT, -- Linking to audit_events
    estado VARCHAR(20) DEFAULT 'ACTIVO', -- ACTIVO, CERRADO, VENCIDO
    INDEX idx_pozo_gate (id_pozo, gate_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
