-- HSE Validations for Test Personnel

USE pna_system;

-- Validaciones automáticas para supervisor
INSERT INTO tbl_validaciones_personal
(id_validacion, id_expediente, id_persona, tipo_validacion, estado_validacion, 
 fecha_vigencia_desde, fecha_vigencia_hasta, fuente, sistema_origen, validado_por) VALUES

('VAL-SUP-MED', 'EXP-TEST-001', 'PER-SUP-001', 'MEDICAL', TRUE,
 CURRENT_DATE, DATE_ADD(CURRENT_DATE, INTERVAL 365 DAY), 'AUTOMATIC', 'Sistema Médico Corporativo', 'SISTEMA'),
 
('VAL-SUP-IND', 'EXP-TEST-001', 'PER-SUP-001', 'INDUCTION', TRUE,
 CURRENT_DATE, DATE_ADD(CURRENT_DATE, INTERVAL 365 DAY), 'AUTOMATIC', 'Sistema HSE', 'SISTEMA'),

-- Validaciones automáticas para operador
('VAL-OP-MED', 'EXP-TEST-001', 'PER-OP-001', 'MEDICAL', TRUE,
 CURRENT_DATE, DATE_ADD(CURRENT_DATE, INTERVAL 365 DAY), 'AUTOMATIC', 'Sistema Médico Corporativo', 'SISTEMA'),
 
('VAL-OP-IND', 'EXP-TEST-001', 'PER-OP-001', 'INDUCTION', TRUE,
 CURRENT_DATE, DATE_ADD(CURRENT_DATE, INTERVAL 365 DAY), 'AUTOMATIC', 'Sistema HSE', 'SISTEMA');

SELECT 'HSE validations seeded successfully' AS status;
