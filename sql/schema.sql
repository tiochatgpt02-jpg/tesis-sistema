-- ============================================================
-- Sistema Educativo IA - Esquema MySQL
-- Ejecutar: python scripts/setup_db.py
-- ============================================================

CREATE DATABASE IF NOT EXISTS sistema_ia
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE sistema_ia;

-- Usuarios (profesores y alumnos)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('teacher', 'student') NOT NULL,
    first_name VARCHAR(100) NOT NULL DEFAULT '',
    last_name VARCHAR(100) NOT NULL DEFAULT '',
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    grade INT,
    student_id INT NULL,
    two_step_code VARCHAR(10),
    two_step_expires DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Estudiantes gestionados por el profesor
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    student_code VARCHAR(30) NULL,
    grade INT NOT NULL,
    section VARCHAR(10) NOT NULL DEFAULT 'A',
    progress INT DEFAULT 0,
    observations TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Temas de aprendizaje por grado
CREATE TABLE IF NOT EXISTS topics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status ENUM('Pendiente', 'En proceso', 'Completado', 'Publicado', 'Privado') DEFAULT 'Pendiente',
    grade INT NOT NULL,
    section VARCHAR(10) NULL,
    unit_number INT NULL,
    session_number INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Progreso académico del estudiante
CREATE TABLE IF NOT EXISTS student_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    overall_progress INT DEFAULT 0,
    completed_topics INT DEFAULT 0,
    study_time VARCHAR(100) DEFAULT '0h',
    average_grade INT DEFAULT 0,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Recomendaciones generadas por IA / ML
CREATE TABLE IF NOT EXISTS ai_recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    title VARCHAR(255),
    summary TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Calificaciones por actividad
CREATE TABLE IF NOT EXISTS grades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    topic_id INT,
    activity_type ENUM('actividades', 'juegos', 'evaluaciones') NOT NULL,
    score INT NOT NULL,
    observations TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL
);

-- Resultados de actividades, juegos y evaluaciones del alumno
CREATE TABLE IF NOT EXISTS student_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    topic_id INT,
    activity_type ENUM('actividades', 'juegos', 'evaluaciones') NOT NULL,
    item_type VARCHAR(100) NOT NULL,
    score DECIMAL(5,2) DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0,
    correct_answers INT DEFAULT 0,
    wrong_answers INT DEFAULT 0,
    notes TEXT,
    time_spent_seconds INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL
);

-- Materiales educativos asignados a cada tema
CREATE TABLE IF NOT EXISTS learning_materials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    material_type ENUM('texto', 'imagen', 'video', 'presentacion', 'documento') NOT NULL,
    description TEXT,
    content TEXT,
    resource_url VARCHAR(500),
    status ENUM('DRAFT', 'PUBLISHED') NOT NULL DEFAULT 'DRAFT',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS material_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT NOT NULL,
    student_id INT NOT NULL,
    reviewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_material_student (material_id, student_id),
    FOREIGN KEY (material_id) REFERENCES learning_materials(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS topic_activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    options JSON,
    correct_answer TEXT,
    score INT DEFAULT 5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS topic_games (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rules TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS topic_evaluations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    difficulty VARCHAR(30) DEFAULT 'media',
    questions JSON NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- Evaluaciones IA con ciclo de aprobación docente (GOAL 3)
CREATE TABLE IF NOT EXISTS assessment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    teacher_id INT NULL,
    title VARCHAR(255) NOT NULL,
    status ENUM('GENERATED', 'PENDING_REVIEW', 'APPROVED', 'PUBLISHED') DEFAULT 'GENERATED',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- Preguntas individuales del assessment con estado de aprobación
CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_id INT NOT NULL,
    question TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    answer TEXT NOT NULL,
    approved BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessment(id) ON DELETE CASCADE
);

-- Intentos de evaluación formal (Examen único de 15 preguntas - GOAL 4)
CREATE TABLE IF NOT EXISTS student_assessment_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    assessment_id INT NOT NULL,
    score DECIMAL(5,2) NOT NULL,
    time_spent INT NOT NULL DEFAULT 0,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    correct_answers INT NOT NULL DEFAULT 0,
    total_questions INT NOT NULL DEFAULT 15,
    percentage DECIMAL(5,2) NOT NULL DEFAULT 0.0,
    reinforce_topics JSON NULL,
    answers JSON NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (assessment_id) REFERENCES assessment(id) ON DELETE CASCADE
);

-- Intentos y resultados de juegos interactivos de reforzamiento (GOAL 5)
CREATE TABLE IF NOT EXISTS student_game_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    game_id INT NOT NULL,
    topic_id INT NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    score DECIMAL(5,2) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    student_answer TEXT NOT NULL,
    time_spent INT NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS topic_presentations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    session_number INT DEFAULT 1,
    status ENUM('DRAFT', 'PUBLISHED') NOT NULL DEFAULT 'DRAFT',
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT DEFAULT 0,
    uploaded_by INT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS student_presentation_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    presentation_id INT NOT NULL,
    student_id INT NOT NULL,
    reviewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_presentation_student (presentation_id, student_id),
    FOREIGN KEY (presentation_id) REFERENCES topic_presentations(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Juegos educativos generados por IA a partir de material del docente (PPTX/TEXT/PDF)
CREATE TABLE IF NOT EXISTS ai_generated_games (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    material_id INT NULL,
    presentation_id INT NULL,
    game_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    instruction TEXT,
    content_json JSON NOT NULL,
    status ENUM('GENERATED', 'PENDING_REVIEW', 'APPROVED', 'PUBLISHED', 'REJECTED') DEFAULT 'PENDING_REVIEW',
    created_by INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES learning_materials(id) ON DELETE SET NULL,
    FOREIGN KEY (presentation_id) REFERENCES topic_presentations(id) ON DELETE SET NULL
);

-- Módulo del profesor: temas generados por IA
CREATE TABLE IF NOT EXISTS teacher_topics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    grade INT NOT NULL,
    status ENUM('Pendiente', 'En proceso', 'Completado', 'Publicado') DEFAULT 'En proceso',
    ai_payload JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS teacher_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS student_submissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    topic_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    status VARCHAR(30) DEFAULT 'pendiente',
    teacher_score DECIMAL(5,2) NULL,
    teacher_feedback TEXT,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- Actividades automáticas asociadas a cada tema
CREATE TABLE IF NOT EXISTS teacher_activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    activity_type ENUM('selección múltiple', 'verdadero/falso', 'completar', 'relacionar', 'ordenar', 'práctica') NOT NULL,
    question TEXT NOT NULL,
    options JSON,
    correct_answer TEXT,
    score INT DEFAULT 5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES teacher_topics(id) ON DELETE CASCADE
);

-- Juegos educativos para cada tema
CREATE TABLE IF NOT EXISTS teacher_games (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rules TEXT,
    is_active BOOLEAN DEFAULT FALSE,
    is_published BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES teacher_topics(id) ON DELETE CASCADE
);

-- Evaluaciones automáticas generadas por IA
CREATE TABLE IF NOT EXISTS teacher_evaluations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    grade INT NOT NULL,
    difficulty ENUM('básica', 'media', 'alta') DEFAULT 'media',
    question_count INT NOT NULL,
    questions JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES teacher_topics(id) ON DELETE CASCADE
);

-- Outcomes académicos reales (target histórico oficial para ML supervisado)
CREATE TABLE IF NOT EXISTS student_academic_outcomes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    academic_year INT NOT NULL,
    period VARCHAR(20) NOT NULL,
    academic_period VARCHAR(30) NULL,
    period_type VARCHAR(30) DEFAULT 'bimester',
    subject VARCHAR(100) NOT NULL DEFAULT 'Computación',
    final_score DECIMAL(5,2) NULL,
    final_grade DECIMAL(5,2) NULL,
    final_percentage DECIMAL(5,2) NULL,
    final_status VARCHAR(30) NULL,
    failed_courses_count INT DEFAULT 0,
    attendance_percentage DECIMAL(5,2) NULL,
    is_at_risk TINYINT(1) DEFAULT 0,
    risk_level VARCHAR(30) NULL,
    risk_reasons TEXT NULL,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    UNIQUE KEY uk_student_period_subject (student_id, academic_year, period, subject)
);

-- Resultado del análisis inteligente de rendimiento por estudiante
CREATE TABLE IF NOT EXISTS student_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    topic_id INT,
    performance_level VARCHAR(50),
    strengths TEXT,
    difficulties TEXT,
    reinforce_topics TEXT,
    risk_level VARCHAR(30),
    recommendations TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES teacher_topics(id) ON DELETE SET NULL
);

-- Recomendaciones de IA del profesor para cada estudiante
CREATE TABLE IF NOT EXISTS teacher_recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    topic_id INT,
    recommendation TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES teacher_topics(id) ON DELETE SET NULL
);

-- ============================================================
-- Datos iniciales (solo si las tablas están vacías)
-- ============================================================

INSERT INTO students (first_name, last_name, grade, progress, observations)
SELECT * FROM (
    SELECT 'Juan',   'Pérez',    5, 20, 'Buen avance en matemáticas. Necesita reforzar lectura.' UNION ALL
    SELECT 'María',  'García',   5, 45, 'Excelente participación en juegos educativos.' UNION ALL
    SELECT 'Carlos', 'López',    4, 65, 'Destaca en evaluaciones de ciencias naturales.' UNION ALL
    SELECT 'Ana',    'Martínez', 6, 80, 'Lista para temas avanzados de fracciones.'
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM students LIMIT 1);

INSERT INTO users (username, password_hash, role, first_name, last_name, email, phone, grade, student_id)
SELECT * FROM (
    SELECT 'alumno1', 'Alumno123', 'student', 'Juan', 'Pérez', 'alumno1@example.com', '+51928251447', 5, 1 UNION ALL
    SELECT 'alumno2', 'Alumno123', 'student', 'María', 'García', 'alumno2@example.com', '+519888251447', 5, 2 UNION ALL
    SELECT 'alumno3', 'Alumno123', 'student', 'Carlos', 'López', 'alumno3@example.com', '+51708251447', 4, 3
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM users LIMIT 1);

INSERT INTO topics (title, description, status, grade)
SELECT * FROM (
    SELECT 'Sumas y restas',           'Operaciones básicas con números hasta 1000.',              'Completado',  4 UNION ALL
    SELECT 'Lectura comprensiva',      'Comprensión de textos cortos con preguntas.',              'En proceso',  4 UNION ALL
    SELECT 'Ecosistemas',              'Conoce los ecosistemas de tu región.',                     'Pendiente',   4 UNION ALL
    SELECT 'Fracciones básicas',       'Introducción a las fracciones y ejercicios básicos.',      'Pendiente',   5 UNION ALL
    SELECT 'Lectura comprensiva',      'Comprensión de textos con inferencias.',                   'En proceso',  5 UNION ALL
    SELECT 'Cuerpo humano',            'Sistemas del cuerpo humano y su función.',                 'Pendiente',   5 UNION ALL
    SELECT 'Fracciones y decimales',   'Operaciones con fracciones y decimales.',                  'En proceso',  6 UNION ALL
    SELECT 'Geometría básica',         'Figuras geométricas, perímetro y área.',                   'Pendiente',   6 UNION ALL
    SELECT 'Historia de México',       'Independencia y reforma.',                               'Completado',  6
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM topics LIMIT 1);

INSERT INTO student_progress (student_id, overall_progress, completed_topics, study_time, average_grade)
SELECT * FROM (
    SELECT 1, 35, 2, '2h 15m', 78 UNION ALL
    SELECT 2, 45, 3, '3h 10m', 85 UNION ALL
    SELECT 3, 65, 4, '4h 00m', 88 UNION ALL
    SELECT 4, 80, 5, '5h 30m', 92
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM student_progress LIMIT 1);

INSERT INTO ai_recommendations (student_id, title, summary)
SELECT * FROM (
    SELECT 1, 'Reforzar fracciones',    'Repasa el tema "Fracciones básicas" con actividades interactivas.' UNION ALL
    SELECT 1, 'Juego recomendado',      'Practica con Memorama de operaciones matemáticas.' UNION ALL
    SELECT 1, 'Siguiente tema',         'Cuando completes fracciones, avanza a "Cuerpo humano".'
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM ai_recommendations LIMIT 1);

INSERT INTO student_notes (student_id, topic_id, activity_type, item_type, score, percentage, correct_answers, wrong_answers, notes, time_spent_seconds, created_at)
SELECT * FROM (
    SELECT 1, 4, 'evaluaciones', 'evaluacion', 7.00,  35.00, 3, 7, 'Evaluación formativa', 320, '2024-03-10 10:00:00' UNION ALL
    SELECT 1, 4, 'actividades',  'actividad',  8.00,  40.00, 4, 6, 'Actividad práctica',   280, '2024-03-18 11:00:00' UNION ALL
    SELECT 1, 5, 'evaluaciones', 'evaluacion', 5.00,  25.00, 2, 8, 'Evaluación bimestral', 400, '2024-03-25 09:30:00' UNION ALL
    SELECT 2, 4, 'evaluaciones', 'evaluacion', 9.50,  47.50, 5, 5, 'Evaluación formativa', 240, '2024-03-10 10:00:00' UNION ALL
    SELECT 2, 4, 'actividades',  'actividad',  10.50, 52.50, 5, 5, 'Actividad práctica',   220, '2024-03-18 11:00:00' UNION ALL
    SELECT 2, 5, 'evaluaciones', 'evaluacion', 10.00, 50.00, 5, 5, 'Evaluación bimestral', 250, '2024-03-25 09:30:00' UNION ALL
    SELECT 3, 1, 'evaluaciones', 'evaluacion', 14.00, 70.00, 7, 3, 'Evaluación formativa', 190, '2024-03-10 10:00:00' UNION ALL
    SELECT 3, 1, 'actividades',  'actividad',  15.00, 75.00, 8, 2, 'Actividad práctica',   180, '2024-03-18 11:00:00' UNION ALL
    SELECT 3, 2, 'evaluaciones', 'evaluacion', 14.50, 72.50, 7, 3, 'Evaluación bimestral', 210, '2024-03-25 09:30:00' UNION ALL
    SELECT 4, 7, 'evaluaciones', 'evaluacion', 18.00, 90.00, 9, 1, 'Evaluación formativa', 150, '2024-03-10 10:00:00' UNION ALL
    SELECT 4, 7, 'actividades',  'actividad',  18.50, 92.50, 9, 1, 'Actividad práctica',   140, '2024-03-18 11:00:00' UNION ALL
    SELECT 4, 8, 'evaluaciones', 'evaluacion', 19.00, 95.00, 10, 0, 'Evaluación bimestral', 130, '2024-03-25 09:30:00'
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM student_notes LIMIT 1);