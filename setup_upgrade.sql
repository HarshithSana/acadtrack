-- ═══════════════════════════════════════════════════════
-- AcadTrack v2 — Database Upgrade Script
-- Run this ONCE in your MySQL database
-- ═══════════════════════════════════════════════════════

-- 1. Predictions table (stores ML prediction results)
CREATE TABLE IF NOT EXISTS Predictions (
    prediction_id   INT AUTO_INCREMENT PRIMARY KEY,
    student_id      VARCHAR(10) NOT NULL,
    predicted_sgpa  DECIMAL(4,2),
    predicted_cgpa  DECIMAL(4,2),
    next_semester   INT,
    confidence      VARCHAR(10),
    predicted_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Students(student_id) ON DELETE CASCADE
);

-- 2. Admins table (if not already created)
CREATE TABLE IF NOT EXISTS Admins (
    admin_id   INT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(50) NOT NULL UNIQUE,
    password   VARCHAR(100) NOT NULL
);

-- 3. Default admin account (change password before going live!)
INSERT IGNORE INTO Admins (username, password) VALUES ('admin', 'admin123');

-- 4. Performance indexes for large datasets
CREATE INDEX IF NOT EXISTS idx_grades_student  ON Grades(student_id);
CREATE INDEX IF NOT EXISTS idx_grades_semester ON Grades(semester_id);
CREATE INDEX IF NOT EXISTS idx_grades_subject  ON Grades(subject_id);
CREATE INDEX IF NOT EXISTS idx_grades_grade    ON Grades(grade);

-- 5. Verify
SELECT 'Predictions table' as item, COUNT(*) as count FROM Predictions
UNION ALL
SELECT 'Admins table', COUNT(*) FROM Admins;