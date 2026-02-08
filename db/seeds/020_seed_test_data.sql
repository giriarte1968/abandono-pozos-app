-- Test Data for Expedientes

USE pna_system;

-- Expediente de prueba
INSERT INTO tbl_expedientes_abandono 
(id_expediente, id_pozo, id_campana, estado_expediente, responsable_tecnico, fecha_inicio_tramite, creado_por) VALUES
('EXP-TEST-001', 'X-TEST-001', 'CAMP-TEST-2026', 'PLANIFICACION_LOGISTICA', 'Ing. Test', CURRENT_DATE, 'SISTEMA');

-- Asignaciones de personal
INSERT INTO tbl_asignaciones_personal 
(id_asignacion, id_expediente, id_persona, rol_en_expediente, es_critico_operacion, fecha_asignacion, asignado_por) VALUES
('ASIG-001', 'EXP-TEST-001', 'PER-SUP-001', 'Supervisor Campo', TRUE, CURRENT_DATE, 'SISTEMA'),
('ASIG-002', 'EXP-TEST-001', 'PER-OP-001', 'Operador Principal', TRUE, CURRENT_DATE, 'SISTEMA');

SELECT 'Test data seeded successfully' AS status;
