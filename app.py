from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from db import execute_query
from ml.predictor import predict_next_sgpa, get_trend
from functools import wraps

app = Flask(__name__)
app.secret_key = 'acadtrack_secret_2024'

# ═══════════════════════════════════════════════
# AUTH DECORATORS
# ═══════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'student_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Admin access required.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ═══════════════════════════════════════════════
# ACADEMIC HELPERS
# ═══════════════════════════════════════════════

def get_sgpa(student_id, semester_id, department):
    """SGPA for one semester — uses Branch_Subjects to filter dept subjects only."""
    rows = execute_query("""
        SELECT s.credits, gp.points
        FROM Grades g
        JOIN Subjects s      ON g.subject_id  = s.subject_id
        JOIN Branch_Subjects bs ON bs.subject_id = s.subject_id
                                AND bs.department = %s
                                AND bs.semester   = g.semester_id
        JOIN GradePoints gp  ON g.grade = gp.grade
        WHERE g.student_id  = %s
          AND g.semester_id = %s
          AND g.grade  != 'F'
          AND s.credits > 0
    """, (department, student_id, semester_id))
    if not rows:
        return 0.0
    tp = sum(float(r['credits']) * float(r['points']) for r in rows)
    tc = sum(float(r['credits']) for r in rows)
    return round(tp / tc, 2) if tc else 0.0

def get_cgpa(student_id, department):
    """CGPA across all semesters — uses Branch_Subjects to filter dept subjects only."""
    rows = execute_query("""
        SELECT s.credits, gp.points
        FROM Grades g
        JOIN Subjects s      ON g.subject_id  = s.subject_id
        JOIN Branch_Subjects bs ON bs.subject_id = s.subject_id
                                AND bs.department = %s
                                AND bs.semester   = g.semester_id
        JOIN GradePoints gp  ON g.grade = gp.grade
        WHERE g.student_id = %s
          AND g.grade != 'F'
          AND s.credits > 0
    """, (department, student_id))
    if not rows:
        return 0.0
    tp = sum(float(r['credits']) * float(r['points']) for r in rows)
    tc = sum(float(r['credits']) for r in rows)
    return round(tp / tc, 2) if tc else 0.0

def get_backlogs(student_id, department):
    """Failed subjects filtered to student's branch subjects only."""
    return execute_query("""
        SELECT s.subject_name, g.semester_id AS semester_number
        FROM Grades g
        JOIN Subjects s      ON g.subject_id  = s.subject_id
        JOIN Branch_Subjects bs ON bs.subject_id = s.subject_id
                                AND bs.department = %s
                                AND bs.semester   = g.semester_id
        WHERE g.student_id = %s
          AND g.grade = 'F'
        ORDER BY g.semester_id
    """, (department, student_id)) or []

def get_semester_data(student_id, department):
    """All completed semesters with SGPA for this student."""
    sems = execute_query("""
        SELECT DISTINCT g.semester_id, g.semester_id AS semester_number
        FROM Grades g
        JOIN Branch_Subjects bs ON bs.subject_id  = g.subject_id
                                AND bs.department = %s
                                AND bs.semester   = g.semester_id
        WHERE g.student_id = %s
        ORDER BY g.semester_id
    """, (department, student_id)) or []

    result = []
    for sem in sems:
        sgpa = get_sgpa(student_id, sem['semester_id'], department)
        result.append({
            'semester_id':     sem['semester_id'],
            'semester_number': sem['semester_number'],
            'sgpa':            sgpa
        })
    return result

def get_dept_rank(student_id, department):
    """Rank within department — single SQL, no loop."""
    rows = execute_query("""
        SELECT
            st.student_id,
            ROUND(
                SUM(CASE WHEN g.grade != 'F' AND s.credits > 0
                         THEN s.credits * gp.points ELSE 0 END)
                /
                NULLIF(SUM(CASE WHEN g.grade != 'F' AND s.credits > 0
                               THEN s.credits ELSE 0 END), 0)
            , 2) AS cgpa
        FROM Students st
        LEFT JOIN Grades g          ON st.student_id  = g.student_id
        LEFT JOIN Subjects s        ON g.subject_id   = s.subject_id
        LEFT JOIN Branch_Subjects bs ON bs.subject_id  = s.subject_id
                                    AND bs.department  = st.department
                                    AND bs.semester    = g.semester_id
        LEFT JOIN GradePoints gp    ON g.grade         = gp.grade
        WHERE st.department = %s
        GROUP BY st.student_id
        ORDER BY cgpa DESC
    """, (department,)) or []

    total = len(rows)
    for i, row in enumerate(rows, 1):
        if row['student_id'] == student_id:
            return i, total
    return None, total

# ═══════════════════════════════════════════════
# STUDENT ROUTES
# ═══════════════════════════════════════════════

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        sid = request.form.get('student_id', '').strip()
        pwd = request.form.get('password', '').strip()
        student = execute_query(
            "SELECT * FROM Students WHERE student_id = %s AND password = %s",
            (sid, pwd)
        )
        if student:
            session['student_id']   = student[0]['student_id']
            session['student_name'] = student[0]['name']
            session['department']   = student[0]['department']
            session['email']        = student[0].get('email', '')
            return redirect(url_for('dashboard'))
        flash('Invalid Roll Number or Password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    sid  = session['student_id']
    dept = session['department']

    cgpa          = get_cgpa(sid, dept)
    backlogs      = get_backlogs(sid, dept)
    semester_data = get_semester_data(sid, dept)
    sgpa_history  = [s['sgpa'] for s in semester_data]

    dept_rank, dept_total = get_dept_rank(sid, dept)

    prediction = None
    trend      = get_trend(sgpa_history)
    if len(sgpa_history) >= 2:
        prediction = predict_next_sgpa(sgpa_history)

    all_grades = execute_query("""
        SELECT g.grade, g.marks, s.subject_name, s.credits,
               g.semester_id AS semester_number, gp.points
        FROM Grades g
        JOIN Subjects s      ON g.subject_id  = s.subject_id
        JOIN Branch_Subjects bs ON bs.subject_id = s.subject_id
                                AND bs.department = %s
                                AND bs.semester   = g.semester_id
        JOIN GradePoints gp  ON g.grade = gp.grade
        WHERE g.student_id = %s
        ORDER BY g.semester_id, s.subject_name
    """, (dept, sid)) or []

    chart_sems     = [f"Sem {s['semester_number']}" for s in semester_data]
    chart_sgpas    = sgpa_history
    chart_subjects = [g['subject_name'][:16] for g in all_grades]
    chart_marks    = [g['marks'] for g in all_grades]

    return render_template('dashboard.html',
        student_name   = session['student_name'],
        student_id     = sid,
        department     = dept,
        email          = session.get('email', ''),
        cgpa           = cgpa,
        backlogs       = backlogs,
        semester_data  = semester_data,
        all_grades     = all_grades,
        dept_rank      = dept_rank,
        dept_total     = dept_total,
        prediction     = prediction,
        trend          = trend,
        chart_sems     = chart_sems,
        chart_sgpas    = chart_sgpas,
        chart_subjects = chart_subjects,
        chart_marks    = chart_marks
    )

@app.route('/semester/<int:sem_number>')
@login_required
def semester_report(sem_number):
    sid  = session['student_id']
    dept = session['department']

    grades = execute_query("""
        SELECT g.grade, g.marks, s.subject_name, s.credits,
               gp.points,
               CASE WHEN g.grade = 'F' OR s.credits = 0 THEN 0
                    ELSE (s.credits * gp.points) END AS grade_points
        FROM Grades g
        JOIN Subjects s      ON g.subject_id  = s.subject_id
        JOIN Branch_Subjects bs ON bs.subject_id = s.subject_id
                                AND bs.department = %s
                                AND bs.semester   = g.semester_id
        JOIN GradePoints gp  ON g.grade = gp.grade
        WHERE g.student_id  = %s
          AND g.semester_id = %s
        ORDER BY s.subject_name
    """, (dept, sid, sem_number)) or []

    if not grades:
        flash(f'No data found for Semester {sem_number}.', 'error')
        return redirect(url_for('dashboard'))

    sgpa     = get_sgpa(sid, sem_number, dept)
    backlogs = [g for g in grades if g['grade'] == 'F']

    earned_credits = sum(
        float(g['credits']) for g in grades
        if g['grade'] != 'F' and float(g['credits']) > 0
    )
    max_credits = sum(
        float(g['credits']) for g in grades
        if float(g['credits']) > 0
    )

    return render_template('semester_report.html',
        student_name   = session['student_name'],
        department     = dept,
        student_id     = sid,
        sem_number     = sem_number,
        grades         = grades,
        sgpa           = sgpa,
        earned_credits = earned_credits,
        max_credits    = max_credits,
        backlogs       = backlogs
    )

# ═══════════════════════════════════════════════
# ADMIN ROUTES
# ═══════════════════════════════════════════════

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        admin = execute_query(
            "SELECT * FROM Admins WHERE username = %s AND password = %s",
            (username, password)
        )
        if admin:
            session['admin_id']   = admin[0]['admin_id']
            session['admin_name'] = admin[0]['username']
            return redirect(url_for('admin_panel'))
        flash('Invalid credentials.', 'error')
    return render_template('admin/admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_panel():
    total_students = execute_query("SELECT COUNT(*) as c FROM Students")[0]['c']
    total_subjects = execute_query("SELECT COUNT(*) as c FROM Subjects")[0]['c']
    total_grades   = execute_query("SELECT COUNT(*) as c FROM Grades")[0]['c']
    dept_stats     = execute_query(
        "SELECT department, COUNT(*) as cnt FROM Students GROUP BY department ORDER BY department"
    ) or []
    backlog_count = execute_query(
        "SELECT COUNT(*) as c FROM Grades WHERE grade = 'F'"
    )[0]['c']

    return render_template('admin/admin_panel.html',
        admin_name     = session['admin_name'],
        total_students = total_students,
        total_subjects = total_subjects,
        total_grades   = total_grades,
        dept_stats     = dept_stats,
        backlog_count  = backlog_count
    )

@app.route('/admin/students')
@admin_required
def manage_students():
    students = execute_query(
        "SELECT * FROM Students ORDER BY department, name"
    ) or []
    return render_template('admin/manage_students.html',
        students   = students,
        admin_name = session['admin_name']
    )

@app.route('/admin/students/add', methods=['POST'])
@admin_required
def add_student():
    execute_query(
        "INSERT INTO Students (student_id, name, email, password, department) VALUES (%s,%s,%s,%s,%s)",
        (request.form['student_id'], request.form['name'], request.form['email'],
         request.form['password'], request.form['department']), fetch=False
    )
    flash(f"Student {request.form['name']} added.", 'success')
    return redirect(url_for('manage_students'))

@app.route('/admin/students/delete/<sid>')
@admin_required
def delete_student(sid):
    execute_query("DELETE FROM Students WHERE student_id = %s", (sid,), fetch=False)
    flash('Student deleted.', 'success')
    return redirect(url_for('manage_students'))

@app.route('/admin/grades')
@admin_required
def manage_grades():
    # Filter by department if selected
    dept_filter = request.args.get('department', '')

    if dept_filter:
        grades = execute_query("""
            SELECT g.grade_id, g.student_id, st.name, st.department,
                   s.subject_name, g.semester_id AS semester_number,
                   g.marks, g.grade
            FROM Grades g
            JOIN Students st  ON g.student_id = st.student_id
            JOIN Subjects s   ON g.subject_id  = s.subject_id
            JOIN Branch_Subjects bs ON bs.subject_id = s.subject_id
                                   AND bs.department = st.department
                                   AND bs.semester   = g.semester_id
            WHERE st.department = %s
            ORDER BY g.semester_id, st.name
        """, (dept_filter,)) or []
    else:
        grades = execute_query("""
            SELECT g.grade_id, g.student_id, st.name, st.department,
                   s.subject_name, g.semester_id AS semester_number,
                   g.marks, g.grade
            FROM Grades g
            JOIN Students st  ON g.student_id = st.student_id
            JOIN Subjects s   ON g.subject_id  = s.subject_id
            JOIN Branch_Subjects bs ON bs.subject_id = s.subject_id
                                   AND bs.department = st.department
                                   AND bs.semester   = g.semester_id
            ORDER BY g.semester_id, st.name
            LIMIT 200
        """) or []

    students  = execute_query("SELECT student_id, name, department FROM Students ORDER BY department, name") or []
    subjects  = execute_query("""
        SELECT DISTINCT s.subject_id, s.subject_name, s.credits, bs.department, bs.semester
        FROM Subjects s
        JOIN Branch_Subjects bs ON bs.subject_id = s.subject_id
        ORDER BY bs.department, bs.semester, s.subject_name
    """) or []
    semesters = execute_query("SELECT * FROM Semesters ORDER BY semester_number") or []
    gpoints   = execute_query("SELECT grade FROM GradePoints ORDER BY points DESC") or []
    departments = execute_query("SELECT DISTINCT department FROM Students ORDER BY department") or []

    return render_template('admin/manage_grades.html',
        grades       = grades,
        students     = students,
        subjects     = subjects,
        semesters    = semesters,
        grade_points = gpoints,
        departments  = departments,
        dept_filter  = dept_filter,
        admin_name   = session['admin_name']
    )

@app.route('/admin/grades/add', methods=['POST'])
@admin_required
def add_grade():
    execute_query(
        "INSERT INTO Grades (student_id, subject_id, semester_id, marks, grade) VALUES (%s,%s,%s,%s,%s)",
        (request.form['student_id'], request.form['subject_id'],
         request.form['semester_id'], request.form['marks'], request.form['grade']),
        fetch=False
    )
    flash('Grade added.', 'success')
    return redirect(url_for('manage_grades'))

@app.route('/admin/grades/delete/<int:gid>')
@admin_required
def delete_grade(gid):
    execute_query("DELETE FROM Grades WHERE grade_id = %s", (gid,), fetch=False)
    flash('Grade deleted.', 'success')
    return redirect(url_for('manage_grades'))

@app.route('/admin/rankings')
@admin_required
def admin_rankings():
    # Single query — CGPA per student using Branch_Subjects for correct subject filtering
    cgpa_rows = execute_query("""
        SELECT
            st.student_id,
            st.name,
            st.department,
            ROUND(
                SUM(CASE WHEN g.grade != 'F' AND s.credits > 0
                         THEN s.credits * gp.points ELSE 0 END)
                /
                NULLIF(SUM(CASE WHEN g.grade != 'F' AND s.credits > 0
                               THEN s.credits ELSE 0 END), 0)
            , 2) AS cgpa
        FROM Students st
        LEFT JOIN Grades g           ON st.student_id  = g.student_id
        LEFT JOIN Subjects s         ON g.subject_id   = s.subject_id
        LEFT JOIN Branch_Subjects bs ON bs.subject_id  = s.subject_id
                                    AND bs.department  = st.department
                                    AND bs.semester    = g.semester_id
        LEFT JOIN GradePoints gp     ON g.grade        = gp.grade
        GROUP BY st.student_id, st.name, st.department
        ORDER BY st.department, cgpa DESC
    """) or []

    backlog_rows = execute_query(
        "SELECT student_id, COUNT(*) AS backlog_count FROM Grades WHERE grade = 'F' GROUP BY student_id"
    ) or []
    backlog_map = {r['student_id']: r['backlog_count'] for r in backlog_rows}

    dept_rankings = {}
    for r in cgpa_rows:
        dept = r['department']
        if dept not in dept_rankings:
            dept_rankings[dept] = []
        dept_rankings[dept].append({
            'student_id': r['student_id'],
            'name':       r['name'],
            'cgpa':       float(r['cgpa']) if r['cgpa'] else 0.0,
            'backlogs':   backlog_map.get(r['student_id'], 0)
        })

    for dept in dept_rankings:
        for i, entry in enumerate(dept_rankings[dept], 1):
            entry['rank'] = i

    return render_template('admin/rankings.html',
        dept_rankings = dept_rankings,
        admin_name    = session['admin_name']
    )

# ═══════════════════════════════════════════════

if __name__ == '__main__':
    app.run(debug=True)