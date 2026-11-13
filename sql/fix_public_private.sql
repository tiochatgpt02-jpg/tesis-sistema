USE sistema_ia;

ALTER TABLE topics
MODIFY COLUMN status
ENUM('Pendiente', 'En proceso', 'Completado', 'Publicado', 'Privado')
DEFAULT 'Pendiente';

CREATE TABLE IF NOT EXISTS topic_presentations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    session_number INT DEFAULT 1,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT DEFAULT 0,
    uploaded_by INT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
