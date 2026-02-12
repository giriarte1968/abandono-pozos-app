-- Migration: 006_closure_quality_export.sql
-- Prompt Maestro: Cierre Técnico + Calidad + Evidencia Certificada + Exportación Regulatoria
-- Principio: Ningún pozo cerrado sin validación técnica + evidencia certificada + calidad aprobada

USE pna_system;

-- ============================================
-- 1. DOCUMENTOS DE EVIDENCIA CERTIFICADA
-- ============================================
CREATE TABLE IF NOT EXISTS tbl_documentos_evidencia (
    documento_evidencia_id INT AUTO_INCREMENT PRIMARY KEY,
    id_pozo VARCHAR(50) NOT NULL,
    tipo_documento VARCHAR(100) NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    url_archivo VARCHAR(500) NOT NULL,
    hash_sha256 VARCHAR(64) NOT NULL,
    tamano_bytes BIGINT NULL,
    mime_type VARCHAR(100) NULL,
    etapa_workflow VARCHAR(50) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'ACTIVO',

    cargado_por VARCHAR(100) NOT NULL,
    cargado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_doc_pozo (id_pozo),
    INDEX idx_doc_tipo (tipo_documento),
    CONSTRAINT chk_doc_estado CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    CONSTRAINT chk_doc_tipo CHECK (tipo_documento IN (
        'CURVA_PRESION', 'REPORTE_CEMENTACION', 'ACTA_CIERRE',
        'FOTO_EVIDENCIA', 'VIDEO_EVIDENCIA', 'CERTIFICADO_HSE',
        'INFORME_INTEGRIDAD', 'OTRO'
    ))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 2. CERTIFICACIÓN DIGITAL
-- ============================================
CREATE TABLE IF NOT EXISTS tbl_certificacion_digital (
    certificacion_digital_id INT AUTO_INCREMENT PRIMARY KEY,
    documento_evidencia_id INT NOT NULL,
    hash_certificacion VARCHAR(64) NOT NULL,
    sello_tiempo_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    firmado_por VARCHAR(100) NOT NULL,
    sistema_origen VARCHAR(50) NOT NULL DEFAULT 'PNA_SYSTEM',
    estado VARCHAR(30) NOT NULL DEFAULT 'VIGENTE',

    FOREIGN KEY (documento_evidencia_id) REFERENCES tbl_documentos_evidencia(documento_evidencia_id),
    INDEX idx_cert_doc (documento_evidencia_id),
    CONSTRAINT chk_cert_estado CHECK (estado IN ('VIGENTE', 'REVOCADA'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 3. CIERRE TÉCNICO DEL POZO
-- ============================================
CREATE TABLE IF NOT EXISTS tbl_cierre_tecnico_pozo (
    cierre_tecnico_pozo_id INT AUTO_INCREMENT PRIMARY KEY,
    id_pozo VARCHAR(50) NOT NULL,
    fecha_inicio_cierre DATE NOT NULL,
    fecha_fin_cierre DATE NULL,
    estado_cierre VARCHAR(30) NOT NULL DEFAULT 'EN_PROCESO',
    aprobado_por VARCHAR(100) NULL,
    fecha_aprobacion DATE NULL,
    dictamen_final TEXT NULL,
    hash_consolidado VARCHAR(64) NULL,

    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creado_por VARCHAR(100) NOT NULL,
    actualizado_en TIMESTAMP NULL,
    actualizado_por VARCHAR(100) NULL,

    INDEX idx_cierre_pozo (id_pozo),
    INDEX idx_cierre_estado (estado_cierre),
    CONSTRAINT chk_cierre_estado CHECK (estado_cierre IN ('EN_PROCESO', 'BLOQUEADO', 'APROBADO', 'CERRADO_DEFENDIBLE'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 4. CHECKLIST DE CIERRE
-- ============================================
CREATE TABLE IF NOT EXISTS tbl_checklist_cierre (
    checklist_cierre_id INT AUTO_INCREMENT PRIMARY KEY,
    cierre_tecnico_pozo_id INT NOT NULL,
    item_control VARCHAR(200) NOT NULL,
    estado_item VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE',
    observacion TEXT NULL,
    validado_por VARCHAR(100) NULL,
    fecha_validacion TIMESTAMP NULL,

    FOREIGN KEY (cierre_tecnico_pozo_id) REFERENCES tbl_cierre_tecnico_pozo(cierre_tecnico_pozo_id),
    INDEX idx_check_cierre (cierre_tecnico_pozo_id),
    CONSTRAINT chk_item_estado CHECK (estado_item IN ('PENDIENTE', 'OK', 'RECHAZADO', 'NO_APLICA'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 5. EXPORTACIÓN REGULATORIA
-- ============================================
CREATE TABLE IF NOT EXISTS tbl_exportacion_regulatoria (
    exportacion_regulatoria_id INT AUTO_INCREMENT PRIMARY KEY,
    id_pozo VARCHAR(50) NOT NULL,
    tipo_regulador VARCHAR(100) NOT NULL,
    formato_generado VARCHAR(50) NOT NULL,
    url_archivo VARCHAR(500) NOT NULL,
    hash_exportacion VARCHAR(64) NOT NULL,
    fecha_generacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    generado_por_sistema VARCHAR(50) NOT NULL DEFAULT 'PNA_SYSTEM',

    INDEX idx_export_pozo (id_pozo),
    INDEX idx_export_formato (formato_generado),
    CONSTRAINT chk_formato CHECK (formato_generado IN ('JSON', 'XML', 'PDF'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 6. ALTER: Vincular cementación con evidencia
-- ============================================
ALTER TABLE tbl_datos_reales_cementacion
    ADD COLUMN id_documento_curva INT NULL,
    ADD COLUMN id_documento_reporte INT NULL;

SELECT 'Closure, quality, and export schema created successfully' AS status;
