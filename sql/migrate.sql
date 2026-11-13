-- Migración: ejecutar en MySQL Workbench si ya tenías una versión anterior
USE sistema_ia;

ALTER TABLE topics MODIFY COLUMN status ENUM('Pendiente', 'En proceso', 'Completado', 'Publicado', 'Privado') DEFAULT 'Pendiente';

-- Ignora errores "Duplicate column" si la columna ya existe
ALTER TABLE users ADD COLUMN first_name VARCHAR(100) NOT NULL DEFAULT '' AFTER role;
ALTER TABLE users ADD COLUMN last_name VARCHAR(100) NOT NULL DEFAULT '' AFTER first_name;
ALTER TABLE users ADD COLUMN student_id INT NULL AFTER grade;

ALTER TABLE students ADD COLUMN observations TEXT AFTER progress;
ALTER TABLE student_progress ADD COLUMN average_grade INT DEFAULT 0 AFTER study_time;

UPDATE users SET first_name = 'Juan', last_name = 'Pérez', student_id = 1 WHERE username = 'alumno1';

-- Outcomes académicos para target supervisado
CREATE TABLE IF NOT EXISTS student_academic_outcomes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    academic_year INT NOT NULL,
    period VARCHAR(20) NOT NULL,
    subject VARCHAR(100) NOT NULL DEFAULT 'Computación',
    final_grade DECIMAL(5,2) NULL,
    final_status VARCHAR(30) NOT NULL,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    INDEX idx_student_outcome (student_id, academic_year, period, subject)
);
