-- Seed Users for Authentication Testing
USE pna_system;

-- Primero aseguramos que Sebastian Cannes existe en el catálogo de personal
INSERT IGNORE INTO tbl_personal_catalogo (id_persona, dni, nombre_completo, rol_principal, es_recurso_critico, activo, creado_por) VALUES
('PER-GER-001', '00000000', 'Sebastian Cannes', 'Gerente', TRUE, TRUE, 'SISTEMA');

-- Insertamos los usuarios (Password por defecto: 123456)
-- Nota: En producción esto sería un hash real.
INSERT INTO tbl_usuarios (username, password_hash, id_persona) VALUES
('sebastian.cannes', '123456', 'PER-GER-001'),
('juan.supervisor', '123456', 'PER-SUP-001'),
('pedro.operador', '123456', 'PER-OP-001'),
('maria.hse', '123456', 'PER-HSE-001'),
('admin', '123456', 'PER-SUP-001'); -- Admin temporalmente como supervisor
