# 🎓 AcadTrack – Student Performance Analytics Platform

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-black)
![MySQL](https://img.shields.io/badge/MySQL-8.x-orange)
![ML](https://img.shields.io/badge/ML-Scikit--Learn-green)
![License](https://img.shields.io/badge/License-Educational-lightgrey)

> A web-based academic performance dashboard for BTech universities, built with Python Flask and MySQL.
> Students can log in to view their grades, SGPA/CGPA, backlogs, department rank, and a machine learning–powered CGPA prediction — all in one place.

---

# 📸 Preview

| Login Page                      | Dashboard                               |
| ------------------------------- | --------------------------------------- |
| ![Login](screenshots/login.png) | ![Dashboard](screenshots/dashboard.png) |

| Semester Report                       | Admin Panel                     |
| ------------------------------------- | ------------------------------- |
| ![Semester](screenshots/semester.png) | ![Admin](screenshots/admin.png) |

---

# ✨ Features

## Student Portal

* 🔐 **Secure Login** — Roll number + password authentication
* 📊 **Live Dashboard** — CGPA, SGPA trend, department rank, subject-wise marks
* 📋 **Semester Reports** — Detailed grade sheet with marks bar, grade distribution chart, printable
* ⚠️ **Backlog Detection** — Automatically detects failed subjects (grade = F) and highlights them
* 🏆 **Department Ranking** — Shows student's rank within their department
* 🤖 **ML CGPA Prediction** — Linear Regression model predicts future CGPA from SGPA history
* 📈 **Performance Trend** — Improving / Declining / Stable badge based on recent SGPA

---

## Admin Portal

* 🔑 **Separate Admin Login** — Independent admin authentication table
* 🗂️ **Manage Students** — Add, view, delete students with live search
* 📝 **Manage Grades** — Add, view, delete grade entries with filters
* 🥇 **Department Rankings** — Full rank table per department with CGPA and backlog info
* 📊 **System Overview** — Statistics on total students, subjects, grade records, and backlogs

---

# 🗂️ Project Structure

```
acadtrack/
├── app.py                        # Main Flask app — all routes
├── db.py                         # MySQL connection helper
├── train_model.py                # ML training script
├── requirements.txt              # Python dependencies
├── setup_upgrade.sql             # DB upgrade script
│
├── ml/
│   └── predictor.py              # Linear Regression prediction logic
│
├── static/
│   └── css/
│       └── style.css             # Main stylesheet
│
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── semester_report.html
│   └── admin/
│        ├── admin_login.html
│        ├── admin_panel.html
│        ├── manage_students.html
│        ├── manage_grades.html
│        └── rankings.html
│
└── screenshots/
    ├── login.png
    ├── dashboard.png
    ├── semester.png
    └── admin.png
```

---

# 🛠️ Tech Stack

| Layer            | Technology                       |
| ---------------- | -------------------------------- |
| Backend          | Python 3.x, Flask                |
| Database         | MySQL 8.x                        |
| Machine Learning | scikit-learn, numpy, joblib      |
| Frontend         | HTML, Jinja2, CSS                |
| Charts           | Chart.js                         |
| Fonts            | Familjen Grotesk, JetBrains Mono |

---

# 🗄️ Database Schema

```
Students        — student_id (PK), name, email, password, department
Subjects        — subject_id (PK), subject_name, credits, semester
Semesters       — semester_id (PK), semester_number
Grades          — grade_id (PK), student_id (FK), subject_id (FK), semester_id (FK), marks, grade
GradePoints     — grade (PK), points
Admins          — admin_id (PK), username, password
Predictions     — prediction_id (PK), student_id (FK), predicted_sgpa, predicted_cgpa, next_semester, confidence
```

---

# 📊 Grade Points

| Grade | Points |
| ----- | ------ |
| O     | 10     |
| A     | 9      |
| B     | 8      |
| C     | 7      |
| D     | 6      |
| F     | 0      |

---

# ⚙️ SGPA / CGPA Calculation

```
SGPA = Σ(Grade Points × Credits) / Σ(Credits)

CGPA = Σ(Grade Points × Credits) / Σ(Credits)  [Across all semesters]
```

Failed subjects (`F`) and zero-credit subjects are excluded from GPA calculations.

---

# 🚀 Installation & Setup

## Prerequisites

* Python 3.9+
* MySQL 8.x
* pip

---

## Step 1 — Install Dependencies

```
pip install -r requirements.txt
```

If scikit-learn fails to install:

```
pip install scikit-learn numpy joblib --upgrade
```

---

## Step 2 — Configure Database

Edit **db.py**

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'yourpassword',
    'database': 'student_db'
}
```

---

## Step 3 — Run Database Upgrade Script

```
source setup_upgrade.sql
```

This creates:

* Admin login table
* ML prediction table
* Performance indexes

---

## Step 4 — Train ML Model

```
python train_model.py
```

Output example:

```
Fetching SGPA histories from database...
Found 60 students with 2+ semesters of data.
Model trained successfully.
```

---

## Step 5 — Run Application

```
python app.py
```

Flask server starts at:

```
http://127.0.0.1:5000
```

---

# 🔐 Default Credentials

### Student Login

```
Roll Number : 237Z1A0501
Password    : 237Z1A0501
```

### Admin Login

```
URL      : http://127.0.0.1:5000/admin/login
Username : admin
Password : admin123
```

⚠️ For production use:

* Change default admin password
* Implement password hashing (bcrypt / Werkzeug)
* Enable HTTPS

---

# 📡 Application Routes

## Student Routes

| Route           | Method   | Description       |
| --------------- | -------- | ----------------- |
| `/`             | GET      | Redirect to login |
| `/login`        | GET/POST | Student login     |
| `/logout`       | GET      | Logout            |
| `/dashboard`    | GET      | Student dashboard |
| `/semester/<n>` | GET      | Semester report   |

---

## Admin Routes

| Route             | Method   | Description         |
| ----------------- | -------- | ------------------- |
| `/admin/login`    | GET/POST | Admin login         |
| `/admin`          | GET      | Admin dashboard     |
| `/admin/students` | GET      | Student management  |
| `/admin/grades`   | GET      | Grade management    |
| `/admin/rankings` | GET      | Department rankings |

---

# 🤖 Machine Learning Module

**Model:** Linear Regression (scikit-learn)

**Inputs**

* Semester number
* Previous SGPA values

**Outputs**

* Predicted SGPA
* Projected CGPA
* Confidence level

Model files:

```
train_model.py
ml/predictor.py
ml/cgpa_model.pkl
```

Prediction is shown only if **2+ semesters of data exist**.

---

# 📊 Dataset

| Item                | Count          |
| ------------------- | -------------- |
| Students            | 60             |
| Subjects            | 69             |
| Semesters with data | 4              |
| Grade records       | 1,980          |
| Departments         | CSE and others |

---

# 🔮 Future Enhancements

* Real-time updates using WebSockets
* Secure password hashing
* Email notifications
* Mobile responsive UI
* Export reports as PDF
* Advanced ML models

---

# 📦 Dependencies

```
Flask
mysql-connector-python
scikit-learn
numpy
joblib
Werkzeug
```

External:

* Chart.js
* Google Fonts

---

# 👨‍💻 Author

Built as a **BTech mini project — Student Academic Performance Analytics System**.

---

# 📄 License

This project is intended for **educational purposes only**.
