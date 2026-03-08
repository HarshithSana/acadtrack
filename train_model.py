"""
train_model.py
--------------
Run this script ONCE to train and save the ML model.

Usage:
    python train_model.py

It connects to MySQL, fetches all students' SGPA history,
trains the Linear Regression model, and saves it to ml/cgpa_model.pkl
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db import execute_query
from ml.predictor import train_model

def get_all_sgpa_histories():
    """Fetch SGPA history for every student from the DB."""
    students = execute_query("SELECT student_id FROM Students")
    if not students:
        print("[ERROR] No students found in DB.")
        return []

    all_histories = []
    for student in students:
        sid = student['student_id']

        # Get semesters this student has data for
        semesters = execute_query("""
            SELECT DISTINCT sem.semester_id, sem.semester_number
            FROM Grades g
            JOIN Semesters sem ON g.semester_id = sem.semester_id
            WHERE g.student_id = %s
            ORDER BY sem.semester_number
        """, (sid,))

        if not semesters or len(semesters) < 2:
            continue

        sgpa_history = []
        for sem in semesters:
            rows = execute_query("""
                SELECT s.credits, gp.points
                FROM Grades g
                JOIN Subjects s ON g.subject_id = s.subject_id
                JOIN GradePoints gp ON g.grade = gp.grade
                WHERE g.student_id = %s AND g.semester_id = %s
            """, (sid, sem['semester_id']))

            if not rows:
                continue
            total_points  = sum(float(r['credits']) * float(r['points']) for r in rows)
            total_credits = sum(float(r['credits']) for r in rows)
            sgpa = round(total_points / total_credits, 2) if total_credits else 0
            sgpa_history.append(sgpa)

        if len(sgpa_history) >= 2:
            all_histories.append(sgpa_history)

    return all_histories


if __name__ == '__main__':
    print("Fetching SGPA histories from database...")
    histories = get_all_sgpa_histories()
    print(f"Found {len(histories)} students with 2+ semesters of data.")

    if not histories:
        print("No data to train on. Make sure your DB has grade records.")
        sys.exit(1)

    model = train_model(histories)
    if model:
        print("✅ Model trained and saved successfully!")
        print("   You can now run: python app.py")
    else:
        print("❌ Training failed.")