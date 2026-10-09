"""
Online Exam & Quiz System - Main Flask Application
Features: User Authentication, Student Exam Engine, Admin Management & Results Analytics.
"""

import os
import sys
import json
import socket
import secrets
from functools import wraps

# Ensure local directory is in Python path (prevents "No module named database" error)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db as db_connect, init_db

app = Flask(__name__)
app.secret_key = "online_exam_super_secret_key_change_in_production"
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Ensure database schema and seed data are initialized on startup
init_db()

# ==========================================
# Database Context & Auto-Closing Connection
# ==========================================

def get_db():
    """Returns database connection stored in Flask request context."""
    if 'db' not in g:
        g.db = db_connect()
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Closes database connection at the end of every request (prevents DB lock error)."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ==========================================
# Authentication & Role Decorators
# ==========================================

def validate_single_session():
    """Checks that the user is logged in and that their session token matches the database."""
    if 'user_id' not in session:
        return False, "Please log in to access this page."
    db = get_db()
    current_user = db.execute("SELECT session_token FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    if not current_user or current_user['session_token'] != session.get('session_token'):
        session.clear()
        return False, "Single Login Policy: You have been logged out because your account was logged in from another device/browser."
    return True, None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_valid, msg = validate_single_session()
        if not is_valid:
            flash(msg, "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_valid, msg = validate_single_session()
        if not is_valid:
            flash(msg, "warning")
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash("Admin access required for this action.", "danger")
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# Public & Auth Routes
# ==========================================

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email = ? OR username = ?",
            (login_identifier, login_identifier)
        ).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            # Generate new session token to invalidate any previous login (Single Logined policy)
            new_session_token = secrets.token_hex(16)
            db.execute("UPDATE users SET session_token = ? WHERE id = ?", (new_session_token, user['id']))
            db.commit()

            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['email'] = user['email']
            session['role'] = user['role']
            session['session_token'] = new_session_token

            flash(f"Welcome back, {user['full_name']}!", "success")
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid email/username or password.", "danger")

    return render_template('login.html')

@app.route('/demo-login/<role>')
def demo_login(role):
    """Quick one-click login for students only. Admin demo login is permanently removed."""
    if role == 'admin':
        flash("Admin Demo Login has been disabled. Admin must log in manually using their private password.", "warning")
        return redirect(url_for('login'))

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE role = 'student' LIMIT 1").fetchone()

    if user:
        new_session_token = secrets.token_hex(16)
        db.execute("UPDATE users SET session_token = ? WHERE id = ?", (new_session_token, user['id']))
        db.commit()

        session['user_id'] = user['id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']
        session['email'] = user['email']
        session['role'] = user['role']
        session['session_token'] = new_session_token

        flash(f"Logged in as Demo Student ({user['full_name']}).", "info")
        return redirect(url_for('student_dashboard'))

    flash("Student account not found. Please register.", "warning")
    return redirect(url_for('login'))

@app.route('/admin/change-password', methods=['GET', 'POST'])
@admin_required
def admin_change_password():
    """Allows admin to change their password so it is known strictly only to himself."""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not current_password or not new_password:
            flash("All password fields are required.", "danger")
            return render_template('admin/change_password.html')

        if new_password != confirm_password:
            flash("New password and confirm password do not match.", "danger")
            return render_template('admin/change_password.html')

        if len(new_password) < 6:
            flash("New password must be at least 6 characters long.", "danger")
            return render_template('admin/change_password.html')

        db = get_db()
        admin_user = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()

        if not admin_user or not check_password_hash(admin_user['password_hash'], current_password):
            flash("Current password is incorrect.", "danger")
            return render_template('admin/change_password.html')

        # Update password and refresh session token
        new_hash = generate_password_hash(new_password)
        new_token = secrets.token_hex(16)
        db.execute("UPDATE users SET password_hash = ?, session_token = ? WHERE id = ?", (new_hash, new_token, session['user_id']))
        db.commit()

        session['session_token'] = new_token
        flash("Admin password updated successfully! Only you now know this password.", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/change_password.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Security: Single Admin policy - all registrations are strictly student accounts
        role = 'student'

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        db = get_db()
        # Check uniqueness
        existing = db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email)
        ).fetchone()

        if existing:
            flash("Username or Email already registered. Please login.", "warning")
            return render_template('register.html')

        hashed_pass = generate_password_hash(password)
        db.execute(
            "INSERT INTO users (username, full_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            (username, full_name, email, hashed_pass, role)
        )
        db.commit()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('login'))

# ==========================================
# Student Routes
# ==========================================

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    db = get_db()
    user_id = session['user_id']

    # Fetch active quizzes
    quizzes = db.execute("""
        SELECT q.*, COUNT(ques.id) AS total_questions,
               SUM(ques.marks) AS total_marks
        FROM quizzes q
        LEFT JOIN questions ques ON q.id = ques.quiz_id
        WHERE q.is_active = 1
        GROUP BY q.id
        ORDER BY q.created_at DESC
    """).fetchall()

    # Fetch past attempts
    attempts = db.execute("""
        SELECT a.*, q.title as quiz_title, q.passing_percentage
        FROM attempts a
        JOIN quizzes q ON a.quiz_id = q.id
        WHERE a.user_id = ?
        ORDER BY a.submitted_at DESC
    """, (user_id,)).fetchall()

    # Statistics
    total_taken = len(attempts)
    passed_count = sum(1 for a in attempts if a['passed'] == 1)
    avg_score = round(sum(a['percentage'] for a in attempts) / total_taken, 1) if total_taken > 0 else 0

    return render_template(
        'student/dashboard.html',
        quizzes=quizzes,
        attempts=attempts,
        total_taken=total_taken,
        passed_count=passed_count,
        avg_score=avg_score
    )

@app.route('/exam/<int:quiz_id>/start')
@login_required
def exam_instructions(quiz_id):
    db = get_db()
    quiz = db.execute("SELECT * FROM quizzes WHERE id = ? AND is_active = 1", (quiz_id,)).fetchone()
    if not quiz:
        flash("Quiz not found or currently inactive.", "danger")
        return redirect(url_for('student_dashboard'))

    questions_count = db.execute(
        "SELECT COUNT(*), COALESCE(SUM(marks), 0) FROM questions WHERE quiz_id = ?",
        (quiz_id,)
    ).fetchone()

    total_questions = questions_count[0]
    total_marks = questions_count[1]

    if total_questions == 0:
        flash("This quiz currently has no questions assigned. Please check back later.", "warning")
        return redirect(url_for('student_dashboard'))

    return render_template(
        'student/start.html',
        quiz=quiz,
        total_questions=total_questions,
        total_marks=total_marks
    )

@app.route('/exam/<int:quiz_id>/take')
@login_required
def take_exam(quiz_id):
    db = get_db()
    quiz = db.execute("SELECT * FROM quizzes WHERE id = ? AND is_active = 1", (quiz_id,)).fetchone()
    if not quiz:
        flash("Quiz not found or not active.", "danger")
        return redirect(url_for('student_dashboard'))

    questions = db.execute(
        "SELECT id, question_text, option_a, option_b, option_c, option_d, marks FROM questions WHERE quiz_id = ? ORDER BY id ASC",
        (quiz_id,)
    ).fetchall()

    if not questions:
        flash("This exam has no questions available yet.", "warning")
        return redirect(url_for('student_dashboard'))

    session[f'exam_started_{quiz_id}'] = True

    return render_template(
        'student/take_exam.html',
        quiz=quiz,
        questions=questions,
        duration_minutes=quiz['duration_minutes']
    )

@app.route('/exam/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_exam(quiz_id):
    db = get_db()
    user_id = session['user_id']

    quiz = db.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,)).fetchone()
    if not quiz:
        flash("Quiz not found.", "danger")
        return redirect(url_for('student_dashboard'))

    questions = db.execute("SELECT * FROM questions WHERE quiz_id = ?", (quiz_id,)).fetchall()
    
    total_marks = sum(q['marks'] for q in questions)
    user_score = 0
    user_answers = {}

    for q in questions:
        field_name = f"question_{q['id']}"
        selected = request.form.get(field_name) # 'A', 'B', 'C', 'D' or None
        user_answers[str(q['id'])] = selected
        if selected and selected.upper() == q['correct_option'].upper():
            user_score += q['marks']

    percentage = round((user_score / total_marks * 100), 2) if total_marks > 0 else 0.0
    passed = 1 if percentage >= quiz['passing_percentage'] else 0
    time_spent = int(request.form.get('time_spent_seconds', 0))

    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO attempts (user_id, quiz_id, score, total_marks, percentage, passed, time_spent_seconds, answers_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        quiz_id,
        user_score,
        total_marks,
        percentage,
        passed,
        time_spent,
        json.dumps(user_answers)
    ))
    attempt_id = cursor.lastrowid
    db.commit()

    flash("Exam submitted successfully! Here is your performance scorecard.", "success")
    return redirect(url_for('exam_result', attempt_id=attempt_id))

@app.route('/exam/result/<int:attempt_id>')
@login_required
def exam_result(attempt_id):
    db = get_db()
    user_id = session['user_id']
    role = session.get('role')

    attempt = db.execute("""
        SELECT a.*, q.title as quiz_title, q.category, q.passing_percentage, u.full_name, u.email
        FROM attempts a
        JOIN quizzes q ON a.quiz_id = q.id
        JOIN users u ON a.user_id = u.id
        WHERE a.id = ?
    """, (attempt_id,)).fetchone()

    if not attempt:
        flash("Result not found.", "danger")
        return redirect(url_for('student_dashboard'))

    # Security check: only candidate or admin can view
    if role != 'admin' and attempt['user_id'] != user_id:
        flash("Access unauthorized for this exam result.", "danger")
        return redirect(url_for('student_dashboard'))

    questions = db.execute("SELECT * FROM questions WHERE quiz_id = ? ORDER BY id ASC", (attempt['quiz_id'],)).fetchall()
    user_answers = json.loads(attempt['answers_json']) if attempt['answers_json'] else {}

    correct_count = 0
    incorrect_count = 0
    unattempted_count = 0

    detailed_review = []
    for q in questions:
        user_ans = user_answers.get(str(q['id']))
        is_correct = (user_ans == q['correct_option'])
        is_skipped = (user_ans is None or user_ans == "")

        if is_skipped:
            unattempted_count += 1
            status = "skipped"
        elif is_correct:
            correct_count += 1
            status = "correct"
        else:
            incorrect_count += 1
            status = "wrong"

        detailed_review.append({
            'question': q,
            'user_choice': user_ans,
            'is_correct': is_correct,
            'is_skipped': is_skipped,
            'status': status
        })

    return render_template(
        'student/result.html',
        attempt=attempt,
        detailed_review=detailed_review,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        unattempted_count=unattempted_count,
        total_questions=len(questions)
    )

@app.route('/exam/certificate/<int:attempt_id>')
@login_required
def certificate(attempt_id):
    db = get_db()
    attempt = db.execute("""
        SELECT a.*, q.title as quiz_title, u.full_name
        FROM attempts a
        JOIN quizzes q ON a.quiz_id = q.id
        JOIN users u ON a.user_id = u.id
        WHERE a.id = ? AND a.passed = 1
    """, (attempt_id,)).fetchone()

    if not attempt:
        flash("Certificate is only available for passed attempts.", "warning")
        return redirect(url_for('student_dashboard'))

    if session.get('role') != 'admin' and attempt['user_id'] != session['user_id']:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('student_dashboard'))

    return render_template('student/certificate.html', attempt=attempt)

# ==========================================
# Admin Routes
# ==========================================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    db = get_db()

    total_quizzes = db.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
    total_students = db.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]
    total_attempts = db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
    avg_score_raw = db.execute("SELECT AVG(percentage) FROM attempts").fetchone()[0]
    avg_score = round(avg_score_raw, 1) if avg_score_raw is not None else 0.0

    quizzes = db.execute("""
        SELECT q.*, COUNT(DISTINCT ques.id) as question_count,
               COUNT(DISTINCT a.id) as attempt_count,
               COALESCE(SUM(ques.marks), 0) as total_marks
        FROM quizzes q
        LEFT JOIN questions ques ON q.id = ques.quiz_id
        LEFT JOIN attempts a ON q.id = a.quiz_id
        GROUP BY q.id
        ORDER BY q.created_at DESC
    """).fetchall()

    recent_attempts = db.execute("""
        SELECT a.*, u.full_name, u.email, q.title as quiz_title
        FROM attempts a
        JOIN users u ON a.user_id = u.id
        JOIN quizzes q ON a.quiz_id = q.id
        ORDER BY a.submitted_at DESC
        LIMIT 6
    """).fetchall()

    return render_template(
        'admin/dashboard.html',
        total_quizzes=total_quizzes,
        total_students=total_students,
        total_attempts=total_attempts,
        avg_score=avg_score,
        quizzes=quizzes,
        recent_attempts=recent_attempts
    )

@app.route('/admin/quiz/new', methods=['GET', 'POST'])
@admin_required
def admin_create_quiz():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'General').strip()
        duration = int(request.form.get('duration_minutes', 15))
        passing_percentage = int(request.form.get('passing_percentage', 50))
        is_active = 1 if request.form.get('is_active') == '1' else 0

        if not title:
            flash("Quiz title is required.", "danger")
            return render_template('admin/quiz_form.html', quiz=None)

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO quizzes (title, description, category, duration_minutes, passing_percentage, is_active, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, description, category, duration, passing_percentage, is_active, session['user_id']))
        new_quiz_id = cursor.lastrowid
        db.commit()

        flash("Quiz created successfully! Now add questions to it.", "success")
        return redirect(url_for('admin_quiz_questions', quiz_id=new_quiz_id))

    return render_template('admin/quiz_form.html', quiz=None)

@app.route('/admin/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_quiz(quiz_id):
    db = get_db()
    quiz = db.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,)).fetchone()
    if not quiz:
        flash("Quiz not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'General').strip()
        duration = int(request.form.get('duration_minutes', 15))
        passing_percentage = int(request.form.get('passing_percentage', 50))
        is_active = 1 if request.form.get('is_active') == '1' else 0

        db.execute("""
            UPDATE quizzes
            SET title = ?, description = ?, category = ?, duration_minutes = ?, passing_percentage = ?, is_active = ?
            WHERE id = ?
        """, (title, description, category, duration, passing_percentage, is_active, quiz_id))
        db.commit()

        flash("Quiz details updated successfully.", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/quiz_form.html', quiz=quiz)

@app.route('/admin/quiz/<int:quiz_id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_quiz(quiz_id):
    db = get_db()
    db.execute("UPDATE quizzes SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?", (quiz_id,))
    db.commit()
    flash("Quiz visibility status toggled.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/quiz/<int:quiz_id>/delete', methods=['POST'])
@admin_required
def admin_delete_quiz(quiz_id):
    db = get_db()
    db.execute("DELETE FROM quizzes WHERE id = ?", (quiz_id,))
    db.commit()
    flash("Quiz and its related questions/attempts have been deleted.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/quiz/<int:quiz_id>/questions')
@admin_required
def admin_quiz_questions(quiz_id):
    db = get_db()
    quiz = db.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,)).fetchone()
    if not quiz:
        flash("Quiz not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    questions = db.execute("SELECT * FROM questions WHERE quiz_id = ? ORDER BY id ASC", (quiz_id,)).fetchall()
    total_marks = sum(q['marks'] for q in questions)

    return render_template('admin/questions.html', quiz=quiz, questions=questions, total_marks=total_marks)

@app.route('/admin/quiz/<int:quiz_id>/questions/add', methods=['POST'])
@admin_required
def admin_add_question(quiz_id):
    q_text = request.form.get('question_text', '').strip()
    opt_a = request.form.get('option_a', '').strip()
    opt_b = request.form.get('option_b', '').strip()
    opt_c = request.form.get('option_c', '').strip()
    opt_d = request.form.get('option_d', '').strip()
    correct_opt = request.form.get('correct_option', 'A').strip().upper()
    explanation = request.form.get('explanation', '').strip()
    marks = int(request.form.get('marks', 1))

    if not all([q_text, opt_a, opt_b, opt_c, opt_d]):
        flash("All question options and question text must be filled.", "danger")
        return redirect(url_for('admin_quiz_questions', quiz_id=quiz_id))

    db = get_db()
    db.execute("""
        INSERT INTO questions (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation, marks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (quiz_id, q_text, opt_a, opt_b, opt_c, opt_d, correct_opt, explanation, marks))
    db.commit()

    flash("New question added successfully!", "success")
    return redirect(url_for('admin_quiz_questions', quiz_id=quiz_id))

@app.route('/admin/question/<int:question_id>/delete', methods=['POST'])
@admin_required
def admin_delete_question(question_id):
    db = get_db()
    question = db.execute("SELECT quiz_id FROM questions WHERE id = ?", (question_id,)).fetchone()
    if question:
        quiz_id = question['quiz_id']
        db.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        db.commit()
        flash("Question deleted.", "info")
        return redirect(url_for('admin_quiz_questions', quiz_id=quiz_id))

    flash("Question not found.", "warning")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/results')
@admin_required
def admin_results():
    db = get_db()
    quiz_filter = request.args.get('quiz_id')

    query = """
        SELECT a.*, u.full_name, u.email, u.username, q.title as quiz_title
        FROM attempts a
        JOIN users u ON a.user_id = u.id
        JOIN quizzes q ON a.quiz_id = q.id
    """
    params = []
    if quiz_filter and quiz_filter.isdigit():
        query += " WHERE a.quiz_id = ?"
        params.append(int(quiz_filter))

    query += " ORDER BY a.submitted_at DESC"

    attempts = db.execute(query, params).fetchall()
    quizzes = db.execute("SELECT id, title FROM quizzes ORDER BY title ASC").fetchall()

    return render_template('admin/results.html', attempts=attempts, quizzes=quizzes, selected_quiz=quiz_filter)

@app.route('/admin/attempt/<int:attempt_id>/delete', methods=['POST'])
@admin_required
def admin_delete_attempt(attempt_id):
    db = get_db()
    db.execute("DELETE FROM attempts WHERE id = ?", (attempt_id,))
    db.commit()
    flash("Attempt record deleted successfully.", "info")
    return redirect(request.referrer or url_for('admin_results'))

# ==========================================
# Run Server
# ==========================================

def get_local_ip():
    """Dynamically get the Wi-Fi/Ethernet IPv4 address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == '__main__':
    init_db()
    port = 5001
    local_ip = get_local_ip()
    print("=" * 60)
    print(f"🎓 Online Exam & Quiz System is running on: http://127.0.0.1:{port}")
    print(f"📱 Mobile access on your Wi-Fi:           http://{local_ip}:{port}")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=port)
