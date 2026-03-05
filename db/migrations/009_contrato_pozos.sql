-- ==========================================
-- MIGRACIÓN 009: TABLA INTERMEDIA CONTRATO-POZOS
-- Normalización de relación many-to-many
-- ==========================================

CREATE TABLE IF NOT EXISTS tbl_contrato_pozos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contrato_id INT NOT NULL,
    pozo_id VARCHAR(50) NOT NULL,
    fecha_asignacion DATE DEFAULT CURRENT_DATE,
    estado ENUM('ACTIVO', 'INACTIVO') DEFAULT 'ACTIVO',
    FOREIGN KEY (contrato_id) REFERENCES CONTRATOS(ID_CONTRATO),
    FOREIGN KEY (pozo_id) REFERENCES tbl_pozos(id_pozo),
    UNIQUE KEY uk_contrato_pozo (contrato_id, pozo_id)
);

CREATE INDEX idx_contrato_pozos_contrato ON tbl_contrato_pozos(contrato_id);
CREATE INDEX idx_contrato_pozos_pozo ON tbl_contrato_pozos(pozo_id);

-- Migración de datos desde campo array pozos_asignados
-- Este script asume que el campo pozos_asignados existe como JSON array en la tabla CONTRATOS
-- En caso de error, ejecutar manualmente la migración basada en los datos del mock

-- NOTA: La migración real de datos se hace en el servicio Python (financial_service_mock.py)
-- para mantener consistencia con los datos mock existentes

SELECT 'Migración 009 completada: tbl_contrato_pozos' AS status;
