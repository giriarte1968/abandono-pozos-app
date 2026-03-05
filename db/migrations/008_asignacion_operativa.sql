-- ==========================================
-- MIGRACIÓN 008: ASIGNACIÓN OPERATIVA DETALLADA
-- Registro de horas reales imputadas por recurso
-- ==========================================

CREATE TABLE IF NOT EXISTS tbl_asignacion_operativa_detalle (
    id_asignacion INT AUTO_INCREMENT PRIMARY KEY,
    id_expediente VARCHAR(50) NOT NULL,
    id_recurso VARCHAR(50) NOT NULL,
    tipo_recurso ENUM('PERSONAL', 'EQUIPO') NOT NULL,
    nombre_recurso VARCHAR(200) NOT NULL,
    fecha_operativa DATE NOT NULL,
    etapa ENUM('LOGISTICA', 'EJECUCION', 'DTM', 'SUPERVISION') NOT NULL,
    tipo_actividad ENUM('TRASLADO', 'OPERACION', 'MONTAJE', 'STANDBY') NOT NULL,
    horas_imputadas DECIMAL(5,2) NOT NULL,
    costo_hora DECIMAL(12,2) NOT NULL,
    costo_total_calculado DECIMAL(14,2) NOT NULL,
    impacto_margen BOOLEAN DEFAULT FALSE,
    observaciones TEXT,
    ts_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_horas_max CHECK (horas_imputadas > 0 AND horas_imputadas <= 12),
    CONSTRAINT chk_standby_impacto CHECK (
        (tipo_actividad = 'STANDBY' AND impacto_margen = TRUE) OR 
        (tipo_actividad != 'STANDBY')
    ),
    CONSTRAINT uq_asignacion UNIQUE (id_expediente, id_recurso, fecha_operativa, etapa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_asignacion_expediente ON tbl_asignacion_operativa_detalle(id_expediente);
CREATE INDEX idx_asignacion_fecha ON tbl_asignacion_operativa_detalle(fecha_operativa);
CREATE INDEX idx_asignacion_recurso ON tbl_asignacion_operativa_detalle(id_recurso);

SELECT 'Migración 008 completada' AS status;
