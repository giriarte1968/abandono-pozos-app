-- Migration: 008_contrato_capacidad_operativa.sql
-- Goal: Technical Capacity Structure for Contracts

USE pna_system;

CREATE TABLE IF NOT EXISTS tbl_contrato_capacidad_operativa (
    id_capacidad INT AUTO_INCREMENT PRIMARY KEY,
    id_contrato INT NOT NULL,
    rol_requerido VARCHAR(100) NOT NULL,
    cantidad_requerida INT NOT NULL,
    tipo_recurso ENUM('PERSONAL', 'EQUIPO') NOT NULL,
    fecha_inicio DATE,
    fecha_fin DATE,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (id_contrato) REFERENCES CONTRATOS(ID_CONTRATO)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert Template for BRACO-YPF-ABANDONO-2026
-- We need to find the ID_CONTRATO first, assuming it's the last one or by name
-- Since this is a migration, we use a subquery

INSERT INTO tbl_contrato_capacidad_operativa (id_contrato, rol_requerido, cantidad_requerida, tipo_recurso)
SELECT ID_CONTRATO, 'PULLING', 3, 'EQUIPO' FROM CONTRATOS WHERE NOMBRE_CONTRATO = 'BRACO-YPF-ABANDONO-2026';

INSERT INTO tbl_contrato_capacidad_operativa (id_contrato, rol_requerido, cantidad_requerida, tipo_recurso)
SELECT ID_CONTRATO, 'CEMENTADOR', 2, 'EQUIPO' FROM CONTRATOS WHERE NOMBRE_CONTRATO = 'BRACO-YPF-ABANDONO-2026';

INSERT INTO tbl_contrato_capacidad_operativa (id_contrato, rol_requerido, cantidad_requerida, tipo_recurso)
SELECT ID_CONTRATO, 'WIRELINE', 1, 'EQUIPO' FROM CONTRATOS WHERE NOMBRE_CONTRATO = 'BRACO-YPF-ABANDONO-2026';

INSERT INTO tbl_contrato_capacidad_operativa (id_contrato, rol_requerido, cantidad_requerida, tipo_recurso)
SELECT ID_CONTRATO, 'SUPERVISION', 2, 'PERSONAL' FROM CONTRATOS WHERE NOMBRE_CONTRATO = 'BRACO-YPF-ABANDONO-2026';

INSERT INTO tbl_contrato_capacidad_operativa (id_contrato, rol_requerido, cantidad_requerida, tipo_recurso)
SELECT ID_CONTRATO, 'WIRELINE', 2, 'PERSONAL' FROM CONTRATOS WHERE NOMBRE_CONTRATO = 'BRACO-YPF-ABANDONO-2026';

INSERT INTO tbl_contrato_capacidad_operativa (id_contrato, rol_requerido, cantidad_requerida, tipo_recurso)
SELECT ID_CONTRATO, 'TRANSP_PERSONAL', 1, 'EQUIPO' FROM CONTRATOS WHERE NOMBRE_CONTRATO = 'BRACO-YPF-ABANDONO-2026';
