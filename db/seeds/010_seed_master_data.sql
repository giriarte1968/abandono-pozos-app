-- Seed Master Data for Testing

USE pna_system;

-- Pozos de prueba
INSERT INTO tbl_pozos (id_pozo, nombre_pozo, id_yacimiento, lat, lon, estado_pozo, creado_por) VALUES
('X-TEST-001', 'Pozo Test 001', 'YAC-LOS-PERALES', -46.5, -68.0, 'ACTIVO', 'SISTEMA'),
('X-TEST-002', 'Pozo Test 002', 'YAC-LOMA-ANCHA', -45.8, -67.5, 'ACTIVO', 'SISTEMA');

-- Campañas
INSERT INTO tbl_campanas (id_campana, nombre_campana, estado_campana, fecha_inicio, creado_por) VALUES
('CAMP-TEST-2026', 'Campaña Test 2026', 'EN_CURSO', '2026-01-01', 'SISTEMA');

-- Personal
INSERT INTO tbl_personal_catalogo (id_persona, dni, nombre_completo, rol_principal, es_recurso_critico, activo, creado_por) VALUES
('PER-SUP-001', '11111111', 'Juan Supervisor', 'Supervisor', TRUE, TRUE, 'SISTEMA'),
('PER-OP-001', '22222222', 'Pedro Operador', 'Operador', TRUE, TRUE, 'SISTEMA'),
('PER-HSE-001', '33333333', 'María HSE', 'HSE', FALSE, TRUE, 'SISTEMA');

-- Equipos
INSERT INTO tbl_equipos_catalogo (id_equipo, nombre_equipo, tipo_equipo, es_critico, activo, creado_por) VALUES
('EQ-PULLING-01', 'Pulling Unit #1', 'PULLING_UNIT', TRUE, TRUE, 'SISTEMA'),
('EQ-CEMENTER-01', 'Cementer #1', 'CEMENTER', TRUE, TRUE, 'SISTEMA');

SELECT 'Master data seeded successfully' AS status;
