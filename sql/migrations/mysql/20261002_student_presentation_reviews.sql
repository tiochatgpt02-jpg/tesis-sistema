CREATE TABLE IF NOT EXISTS student_presentation_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    presentation_id INT NOT NULL,
    student_id INT NOT NULL,
    reviewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_presentation_student (presentation_id, student_id),
    FOREIGN KEY (presentation_id) REFERENCES topic_presentations(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);
