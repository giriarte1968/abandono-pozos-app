-- Migration: 004_regulatory_compliance.sql
-- Motor de Cumplimiento Regulatorio Versionado
-- Principios: Multi-jurisdicción, Inmutabilidad de reglas vigentes, Trazabilidad completa

USE pna_system;

-- ============================================
-- 1. JURISDICCIONES
-- ============================================
CREATE TABLE IF NOT EXISTS tbl_jurisdiccion (
    jurisdiccion_id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    pais VARCHAR(100) NOT NULL,
    provincia VARCHAR(100) NULL,
    activo CHAR(1) DEFAULT 'S',

    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creado_por VARCHAR(100) NOT NULL,
    actualizado_en TIMESTAMP NULL,
    actualizado_por VARCHAR(100) NULL,

    INDEX idx_jurisdiccion_pais (pais),
    CONSTRAINT chk_jurisdiccion_activo CHECK (activo IN ('S', 'N'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 2. VERSIONES DE REGULACIÓN
-- ============================================
CREATE TABLE IF NOT EXISTS tbl_version_regulacion (
    version_regulacion_id INT AUTO_INCREMENT PRIMARY KEY,
    jurisdiccion_id INT NOT NULL,
    nombre_version VARCHAR(100) NOT NULL,
    fecha_vigencia_desde DATE NOT NULL,
    fecha_vigencia_hasta DATE NULL,
    estado VARCHAR(20) NOT NULL,

    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creado_por VARCHAR(100) NOT NULL,
    actualizado_en TIMESTAMP NULL,
    actualizado_por VARCHAR(100) NULL,

    FOREIGN KEY (jurisdiccion_id) REFERENCES tbl_jurisdiccion(jurisdiccion_id),
    INDEX idx_version_jurisdiccion (jurisdiccion_id),
    INDEX idx_version_estado (estado),
    CONSTRAINT chk_version_estado CHECK (estado IN ('BORRADOR', 'VIGENTE', 'ARCHIVADA'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 3. REGLAS REGULATORIAS
-- ============================================
CREATE TABLE IF NOT EXISTS tbl_regla_regulatoria (
    regla_regulatoria_id INT AUTO_INCREMENT PRIMARY KEY,
    version_regulacion_id INT NOT NULL,
    codigo_regla VARCHAR(50) NOT NULL,
    descripcion VARCHAR(500) NOT NULL,
    tipo_regla VARCHAR(30) NOT NULL,
    parametro VARCHAR(100) NOT NULL,
    valor_minimo DECIMAL(15,4) NULL,
    valor_maximo DECIMAL(15,4) NULL,
    unidad VARCHAR(50) NULL,
    es_bloqueante CHAR(1) DEFAULT 'S',
    severidad VARCHAR(20) NOT NULL,

    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creado_por VARCHAR(100) NOT NULL,
    actualizado_en TIMESTAMP NULL,
    actualizado_por VARCHAR(100) NULL,

    FOREIGN KEY (version_regulacion_id) REFERENCES tbl_version_regulacion(version_regulacion_id),
    INDEX idx_regla_version (version_regulacion_id),
    CONSTRAINT chk_tipo_regla CHECK (tipo_regla IN ('VALOR_MINIMO', 'VALOR_MAXIMO', 'RANGO', 'REQUERIDO', 'BOOLEANO')),
    CONSTRAINT chk_regla_severidad CHECK (severidad IN ('INFO', 'ADVERTENCIA', 'ERROR')),
    CONSTRAINT chk_regla_bloqueante CHECK (es_bloqueante IN ('S', 'N'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 4. ASIGNACIÓN REGULACIÓN ↔ POZO
-- ============================================
CREATE TABLE IF NOT EXISTS tbl_asignacion_regulacion_pozo (
    asignacion_regulacion_pozo_id INT AUTO_INCREMENT PRIMARY KEY,
    pozo_id VARCHAR(50) NOT NULL,
    version_regulacion_id INT NOT NULL,
    asignado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    asignado_por VARCHAR(100) NOT NULL,

    FOREIGN KEY (version_regulacion_id) REFERENCES tbl_version_regulacion(version_regulacion_id),
    INDEX idx_asignacion_pozo (pozo_id),
    INDEX idx_asignacion_version (version_regulacion_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 5. RESULTADOS DE CUMPLIMIENTO
-- ============================================
CREATE TABLE IF NOT EXISTS tbl_resultado_cumplimiento (
    resultado_cumplimiento_id INT AUTO_INCREMENT PRIMARY KEY,
    pozo_id VARCHAR(50) NOT NULL,
    regla_regulatoria_id INT NOT NULL,
    etapa_evaluada VARCHAR(50) NOT NULL,
    valor_evaluado VARCHAR(200) NOT NULL,
    valor_minimo_esperado DECIMAL(15,4) NULL,
    valor_maximo_esperado DECIMAL(15,4) NULL,
    estado VARCHAR(20) NOT NULL,
    override_aplicado CHAR(1) DEFAULT 'N',
    motivo_override VARCHAR(500) NULL,
    usuario_override VARCHAR(100) NULL,
    vencimiento_override DATE NULL,
    evaluado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (regla_regulatoria_id) REFERENCES tbl_regla_regulatoria(regla_regulatoria_id),
    INDEX idx_resultado_pozo (pozo_id),
    INDEX idx_resultado_estado (estado),
    CONSTRAINT chk_resultado_estado CHECK (estado IN ('CUMPLE', 'NO_CUMPLE', 'ADVERTENCIA')),
    CONSTRAINT chk_resultado_override CHECK (override_aplicado IN ('S', 'N'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT 'Regulatory compliance schema created successfully' AS status;
