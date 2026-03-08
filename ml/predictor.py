"""
ml/predictor.py
---------------
Linear Regression model for predicting future CGPA.
- train_model()  : trains on all students' SGPA history, saves model
- predict_cgpa() : loads saved model, returns predicted next SGPA + projected CGPA
"""

import os
import numpy as np
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'cgpa_model.pkl')

# ─────────────────────────────────────────
# TRAINING
# ─────────────────────────────────────────

def train_model(all_student_sgpa_data):
    """
    Train a Linear Regression model on SGPA history.

    Parameters
    ----------
    all_student_sgpa_data : list of lists
        Each inner list = [sgpa_sem1, sgpa_sem2, sgpa_sem3, ...] for one student.
        All students with >= 2 semesters are used.

    Example input:
        [[6.8, 7.2, 7.5, 7.0], [8.1, 8.3, 8.0, 8.6], ...]
    """
    from sklearn.linear_model import LinearRegression

    X, y = [], []
    for sgpa_list in all_student_sgpa_data:
        if len(sgpa_list) < 2:
            continue
        for i in range(1, len(sgpa_list)):
            # Features: semester index + all previous SGPAs (padded to max 8)
            prev = sgpa_list[:i]
            padded = prev + [0.0] * (8 - len(prev))
            features = [i] + padded          # [sem_number, s1, s2, ..., s8]
            X.append(features)
            y.append(sgpa_list[i])

    if not X:
        print("[ML] Not enough data to train.")
        return None

    X = np.array(X)
    y = np.array(y)

    model = LinearRegression()
    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)
    print(f"[ML] Model trained on {len(X)} samples. Saved to {MODEL_PATH}")
    return model


# ─────────────────────────────────────────
# PREDICTION
# ─────────────────────────────────────────

def predict_next_sgpa(sgpa_history):
    """
    Predict next semester SGPA given a student's SGPA history.

    Parameters
    ----------
    sgpa_history : list of floats
        e.g. [6.8, 7.2, 7.5]  (semesters 1, 2, 3)

    Returns
    -------
    dict with keys:
        predicted_sgpa   : float  — next semester predicted SGPA
        predicted_cgpa   : float  — projected CGPA including prediction
        confidence       : str    — 'high' / 'medium' / 'low'
        next_semester    : int    — which semester is being predicted
    """
    if len(sgpa_history) < 2:
        return None  # Not enough data

    if not os.path.exists(MODEL_PATH):
        return None  # Model not trained yet

    model = joblib.load(MODEL_PATH)

    next_sem = len(sgpa_history) + 1
    padded = sgpa_history + [0.0] * (8 - len(sgpa_history))
    features = np.array([[next_sem] + padded])

    raw_pred = float(model.predict(features)[0])
    # Clamp to valid SGPA range
    predicted_sgpa = round(max(0.0, min(10.0, raw_pred)), 2)

    # Projected CGPA = average of all SGPAs including prediction
    all_sgpas = sgpa_history + [predicted_sgpa]
    predicted_cgpa = round(sum(all_sgpas) / len(all_sgpas), 2)

    # Confidence based on data points available
    n = len(sgpa_history)
    confidence = 'high' if n >= 3 else 'medium' if n == 2 else 'low'

    return {
        'predicted_sgpa': predicted_sgpa,
        'predicted_cgpa': predicted_cgpa,
        'confidence': confidence,
        'next_semester': next_sem
    }


# ─────────────────────────────────────────
# TREND ANALYSIS
# ─────────────────────────────────────────

def get_trend(sgpa_history):
    """
    Returns 'improving', 'declining', or 'stable' based on SGPA history.
    """
    if len(sgpa_history) < 2:
        return 'stable'
    delta = sgpa_history[-1] - sgpa_history[-2]
    if delta > 0.2:
        return 'improving'
    elif delta < -0.2:
        return 'declining'
    return 'stable'