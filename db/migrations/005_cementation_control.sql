-- Migration: 005_cementation_control.sql
-- Módulo 2: Control Inteligente de Parámetros de Cementación
-- Principio: Diseño aprobado (Ingeniería) vs Datos reales bombeados (Proveedor)

USE pna_system;

-- ============================================
-- 1. DISEÑO DE CEMENTACIÓN (Aprobado por Ingeniería)
-- ============================================
CREATE TABLE IF NOT EXISTS tbl_diseno_cementacion (
    diseno_cementacion_id INT AUTO_INCREMENT PRIMARY KEY,
    id_pozo VARCHAR(50) NOT NULL,
    volumen_teorico_m3 DECIMAL(10,2) NOT NULL,
    densidad_objetivo_ppg DECIMAL(5,2) NOT NULL,
    presion_maxima_permitida_psi DECIMAL(10,2) NOT NULL,
    intervalo_desde_m DECIMAL(10,2) NOT NULL,
    intervalo_hasta_m DECIMAL(10,2) NOT NULL,
    tipo_lechada VARCHAR(100) NOT NULL,
    fecha_aprobacion DATE NULL,
    aprobado_por VARCHAR(100) NULL,
    estado_diseno VARCHAR(30) NOT NULL DEFAULT 'BORRADOR',

    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creado_por VARCHAR(100) NOT NULL,
    actualizado_en TIMESTAMP NULL,
    actualizado_por VARCHAR(100) NULL,

    INDEX idx_diseno_pozo (id_pozo),
    INDEX idx_diseno_estado (estado_diseno),
    CONSTRAINT chk_diseno_estado CHECK (estado_diseno IN ('BORRADOR', 'APROBADO', 'INACTIVO')),
    CONSTRAINT chk_diseno_intervalo CHECK (intervalo_hasta_m > intervalo_desde_m)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 2. DATOS REALES DE CEMENTACIÓN (Cargados por Proveedor)
-- ============================================
CREATE TABLE IF NOT EXISTS tbl_datos_reales_cementacion (
    dato_real_cementacion_id INT AUTO_INCREMENT PRIMARY KEY,
    diseno_cementacion_id INT NOT NULL,
    volumen_real_m3 DECIMAL(10,2) NOT NULL,
    densidad_real_ppg DECIMAL(5,2) NOT NULL,
    presion_maxima_registrada_psi DECIMAL(10,2) NOT NULL,
    tiempo_bombeo_min DECIMAL(10,2) NULL,
    archivo_curva_url VARCHAR(500) NULL,
    proveedor_servicio VARCHAR(150) NOT NULL,
    fecha_ejecucion DATE NOT NULL,
    cargado_por VARCHAR(100) NOT NULL,

    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (diseno_cementacion_id) REFERENCES tbl_diseno_cementacion(diseno_cementacion_id),
    INDEX idx_datos_diseno (diseno_cementacion_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 3. VALIDACIÓN AUTOMÁTICA DE CEMENTACIÓN
-- ============================================
CREATE TABLE IF NOT EXISTS tbl_validacion_cementacion (
    validacion_cementacion_id INT AUTO_INCREMENT PRIMARY KEY,
    dato_real_cementacion_id INT NOT NULL,
    desvio_volumen_pct DECIMAL(5,2) NOT NULL,
    desvio_densidad_pct DECIMAL(5,2) NOT NULL,
    exceso_presion VARCHAR(5) NOT NULL,
    resultado_validacion VARCHAR(20) NOT NULL,
    fecha_validacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    validado_por_sistema VARCHAR(50) NOT NULL DEFAULT 'MOTOR_CEMENTACION',

    override_aplicado CHAR(1) DEFAULT 'N',
    motivo_override VARCHAR(500) NULL,
    usuario_override VARCHAR(100) NULL,
    vencimiento_override DATE NULL,

    FOREIGN KEY (dato_real_cementacion_id) REFERENCES tbl_datos_reales_cementacion(dato_real_cementacion_id),
    INDEX idx_validacion_dato (dato_real_cementacion_id),
    INDEX idx_validacion_resultado (resultado_validacion),
    CONSTRAINT chk_validacion_resultado CHECK (resultado_validacion IN ('OK', 'ALERTA', 'CRITICO')),
    CONSTRAINT chk_exceso_presion CHECK (exceso_presion IN ('SI', 'NO')),
    CONSTRAINT chk_override_cem CHECK (override_aplicado IN ('S', 'N'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 4. EVENTOS DE CEMENTACIÓN (Trazabilidad Inmutable)
-- ============================================
CREATE TABLE IF NOT EXISTS tbl_eventos_cementacion (
    evento_cementacion_id INT AUTO_INCREMENT PRIMARY KEY,
    id_pozo VARCHAR(50) NOT NULL,
    tipo_evento VARCHAR(50) NOT NULL,
    detalle_evento TEXT NOT NULL,
    fecha_evento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario_evento VARCHAR(100) NOT NULL,

    INDEX idx_evento_cem_pozo (id_pozo),
    INDEX idx_evento_cem_tipo (tipo_evento),
    CONSTRAINT chk_tipo_evento_cem CHECK (tipo_evento IN (
        'DISENO_APROBADO', 'DATOS_CARGADOS', 'VALIDACION_OK',
        'VALIDACION_ALERTA', 'VALIDACION_CRITICA', 'OVERRIDE_MANUAL'
    ))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT 'Cementation control schema created successfully' AS status;
