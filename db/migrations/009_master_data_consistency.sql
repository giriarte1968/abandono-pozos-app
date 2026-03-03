-- Migration: 009_master_data_consistency.sql
-- Goal: Ensure master data consistency for Braco Energy / YPF operations
-- Roles: WIRELINE, TRANSP_PERSONAL, TRANSP_AGUA, TRANSP_COMBUSTIBLE, SUPERVISION

USE pna_system;

-- 1. Insert New Contract for YPF
INSERT INTO CONTRATOS (NOMBRE_CONTRATO, CLIENTE, CANTIDAD_POZOS, VALOR_UNITARIO_BASE_USD, MONTO_TOTAL_CONTRACTUAL, BACKLOG_RESTANTE, PLAZO_PAGO_DIAS, FECHA_INICIO, FECHA_FIN, ESTADO)
VALUES ('BRACO-YPF-ABANDONO-2026', 'YPF', 700, 150000.00, 105000000.00, 105000000.00, 45, '2026-01-01', '2030-12-31', 'ACTIVO')
ON DUPLICATE KEY UPDATE NOMBRE_CONTRATO=VALUES(NOMBRE_CONTRATO);

-- 2. Insert Personal Catalog with New Roles
INSERT INTO tbl_personal_catalogo (id_persona, dni, nombre_completo, rol_principal, es_recurso_critico, activo, creado_por) VALUES
('PER-WRL-001', '40111222', 'Carlos Wireline', 'WIRELINE', TRUE, TRUE, 'SISTEMA'),
('PER-WRL-002', '40222333', 'Ana Wireline', 'WIRELINE', TRUE, TRUE, 'SISTEMA'),
('PER-TRP-001', '40333444', 'Juan Chofer', 'TRANSP_PERSONAL', FALSE, TRUE, 'SISTEMA'),
('PER-TRP-002', '40444555', 'Luis Chofer', 'TRANSP_PERSONAL', FALSE, TRUE, 'SISTEMA'),
('PER-TRW-001', '40555666', 'Jose Agua', 'TRANSP_AGUA', FALSE, TRUE, 'SISTEMA'),
('PER-TRF-001', '40666777', 'Mario Fuel', 'TRANSP_COMBUSTIBLE', FALSE, TRUE, 'SISTEMA'),
('PER-SUP-002', '40777888', 'Sebastian Supervisor', 'SUPERVISION', TRUE, TRUE, 'SISTEMA')
ON DUPLICATE KEY UPDATE nombre_completo=VALUES(nombre_completo);

-- 3. Insert Equipment Catalog with New Types
INSERT INTO tbl_equipos_catalogo (id_equipo, nombre_equipo, tipo_equipo, brand, model, serial_number, es_critico, activo, creado_por) VALUES
('EQ-WRL-01', 'Wireline Unit #1', 'WIRELINE_UNIT', 'Halliburton', 'W-2025', 'SN-WRL-001', TRUE, TRUE, 'SISTEMA'),
('EQ-WRL-02', 'Wireline Unit #2', 'WIRELINE_UNIT', 'Halliburton', 'W-2025', 'SN-WRL-002', TRUE, TRUE, 'SISTEMA'),
('EQ-TAG-01', 'Cisterna Agua 25m3', 'CISTERNA_AGUA', 'Iveco', 'Trakker', 'SN-TAG-001', FALSE, TRUE, 'SISTEMA'),
('EQ-TCM-01', 'Cisterna Combustible', 'CISTERNA_COMBUSTIBLE', 'Mercedes', 'Axor', 'SN-TCM-001', FALSE, TRUE, 'SISTEMA'),
('EQ-MBP-01', 'Minibus Personal', 'MINIBUS_PERSONAL', 'Mercedes', 'Sprinter', 'SN-MBP-001', FALSE, TRUE, 'SISTEMA')
ON DUPLICATE KEY UPDATE nombre_equipo=VALUES(nombre_equipo);
