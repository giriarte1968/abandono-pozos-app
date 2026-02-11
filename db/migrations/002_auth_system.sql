-- Migration 002: Authentication System
USE pna_system;

CREATE TABLE IF NOT EXISTS tbl_usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    id_persona VARCHAR(50) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (id_persona) REFERENCES tbl_personal_catalogo(id_persona)
);

CREATE INDEX idx_usuarios_username ON tbl_usuarios(username);
