-- Migración 001: Crear tabla student_academic_outcomes para target supervisado
USE sistema_ia;

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
