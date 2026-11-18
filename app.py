
from flask import Flask, render_template, request, redirect, url_for, session, render_template_string
import sqlite3
import os
import re
import random
import uuid

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from pypdf import PdfReader
from docx import Document
from pptx import Presentation

from question_bank import QUESTION_BANK


app = Flask(__name__)
app.secret_key = "aeolp_secret_key_2026"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

os.makedirs("instance", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

DATABASE = os.path.join("instance", "aeolp.db")

ALLOWED_EXTENSIONS = {"pdf", "txt", "docx", "pptx"}


# DATABASE

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():

    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            python TEXT NOT NULL,
            data_analysis TEXT NOT NULL,
            machine_learning TEXT NOT NULL,
            statistics TEXT NOT NULL,
            gaps TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            stored_name TEXT NOT NULL,
            extracted_text TEXT NOT NULL,
            uploaded_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_name TEXT,
            score INTEGER,
            total INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS adaptive_quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            difficulty TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    demo_users = [
        ("learner@aeolp.com", "Learner@123", "learner"),
        ("trainer@aeolp.com", "Trainer@123", "trainer"),
        ("admin@aeolp.com", "Admin@123", "admin")
    ]

    for email, password, role in demo_users:

        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing is None:

            conn.execute(
                "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
                (email, generate_password_hash(password), role)
            )

    conn.commit()
    conn.close()


# HOME

@app.route('/')
def home():
    return render_template('index.html')


# LOGIN

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND role = ?",
            (email, role)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user['password'], password):

            session['user_id'] = user['id']
            session['email'] = user['email']
            session['role'] = user['role']

            if role == 'learner':
                return redirect(url_for('learner_dashboard'))

            if role == 'trainer':
                return redirect(url_for('trainer_dashboard'))

            if role == 'admin':
                return redirect(url_for('admin_dashboard'))

        return "Invalid Email, Password or Role."

    return render_template('login.html')


# DASHBOARDS

@app.route('/learner-dashboard')
def learner_dashboard():

    if 'user_id' not in session or session['role'] != 'learner':
        return redirect(url_for('login'))

    return render_template('learner_dashboard.html')


@app.route('/trainer-dashboard')
def trainer_dashboard():

    if 'user_id' not in session or session['role'] != 'trainer':
        return redirect(url_for('login'))

    return render_template('trainer_dashboard.html')


@app.route('/admin-dashboard')
def admin_dashboard():

    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    return render_template('admin_dashboard.html')


# ADMIN USER MANAGEMENT

@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    message = ""

    conn = get_db_connection()

    if request.method == 'POST':

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', '')

        if not email:
            message = "Email is required."

        elif role not in ['learner', 'trainer']:
            message = "Invalid role selected."

        elif len(password) < 8:
            message = "Password must contain at least 8 characters."

        else:

            try:

                conn.execute("""
                    INSERT INTO users (email, password, role)
                    VALUES (?, ?, ?)
                """, (
                    email,
                    generate_password_hash(password),
                    role
                ))

                conn.commit()
                message = "Account created successfully!"

            except sqlite3.IntegrityError:
                message = "Email already exists."

    users = conn.execute("""
        SELECT id, email, role
        FROM users
        ORDER BY id DESC
    """).fetchall()

    learner_count = conn.execute("""
        SELECT COUNT(*) FROM users WHERE role = 'learner'
    """).fetchone()[0]

    trainer_count = conn.execute("""
        SELECT COUNT(*) FROM users WHERE role = 'trainer'
    """).fetchone()[0]

    conn.close()

    return render_template_string("""
    <html>
    <head>
        <title>Manage Users</title>
    </head>
    <body>

        <h1>Manage Users - AEOLP</h1>

        <h3>Total Learners: {{ learner_count }}</h3>
        <h3>Total Trainers: {{ trainer_count }}</h3>

        <p>{{ message }}</p>

        <h2>Create User Account</h2>

        <form method="POST">

            <label>Email:</label>
            <input type="email" name="email" required>
            <br><br>

            <label>Password:</label>
            <input type="password" name="password" minlength="8" required>
            <br><br>

            <label>Role:</label>

            <select name="role" required>
                <option value="">Select Role</option>
                <option value="learner">Learner</option>
                <option value="trainer">Trainer</option>
            </select>

            <br><br>

            <button type="submit">Create Account</button>

        </form>

        <h2>Registered Users</h2>

        <table border="1" cellpadding="8">
            <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Role</th>
            </tr>

            {% for user in users %}
            <tr>
                <td>{{ user.id }}</td>
                <td>{{ user.email }}</td>
                <td>{{ user.role }}</td>
            </tr>
            {% endfor %}
        </table>

        <br>
        <a href="/admin-dashboard">Back to Admin Dashboard</a>

    </body>
    </html>
    """,
    users=users,
    learner_count=learner_count,
    trainer_count=trainer_count,
    message=message)


# ADMIN ANALYTICS

@app.route('/admin/analytics')
def admin_analytics():

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()

    total_users = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    learners = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'learner'"
    ).fetchone()[0]

    trainers = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'trainer'"
    ).fetchone()[0]

    admins = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'admin'"
    ).fetchone()[0]

    total_materials = conn.execute(
        "SELECT COUNT(*) FROM materials"
    ).fetchone()[0]

    total_material_quizzes = conn.execute(
        "SELECT COUNT(*) FROM quiz_results"
    ).fetchone()[0]

    total_adaptive_quizzes = conn.execute(
        "SELECT COUNT(*) FROM adaptive_quiz_results"
    ).fetchone()[0]

    material_average = conn.execute("""
        SELECT AVG(score * 100.0 / total)
        FROM quiz_results
        WHERE total > 0
    """).fetchone()[0]

    adaptive_average = conn.execute("""
        SELECT AVG(score * 100.0 / total)
        FROM adaptive_quiz_results
        WHERE total > 0
    """).fetchone()[0]

    conn.close()

    material_average = round(material_average, 1) if material_average is not None else 0
    adaptive_average = round(adaptive_average, 1) if adaptive_average is not None else 0

    return render_template_string("""
    <html>
    <head>
        <title>Platform Analytics</title>
    </head>
    <body>

        <h1>AEOLP Platform Analytics</h1>

        <h2>User Statistics</h2>
        <p>Total Users: {{ total_users }}</p>
        <p>Learners: {{ learners }}</p>
        <p>Trainers: {{ trainers }}</p>
        <p>Admins: {{ admins }}</p>

        <hr>

        <h2>Learning Statistics</h2>
        <p>Total Learning Materials: {{ total_materials }}</p>
        <p>Material Quiz Attempts: {{ total_material_quizzes }}</p>
        <p>Adaptive Quiz Attempts: {{ total_adaptive_quizzes }}</p>

        <hr>

        <h2>Quiz Performance</h2>
        <p>Average Material Quiz Score: {{ material_average }}%</p>
        <p>Average Adaptive Quiz Score: {{ adaptive_average }}%</p>

        <br>
        <a href="/admin-dashboard">Back to Admin Dashboard</a>

    </body>
    </html>
    """,
    total_users=total_users,
    learners=learners,
    trainers=trainers,
    admins=admins,
    total_materials=total_materials,
    total_material_quizzes=total_material_quizzes,
    total_adaptive_quizzes=total_adaptive_quizzes,
    material_average=material_average,
    adaptive_average=adaptive_average)


# ADMIN LEARNER PROGRESS

@app.route('/admin/learner-progress')
def admin_learner_progress():

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()

    learners = conn.execute("""
        SELECT
            u.id,
            u.email,

            (
                SELECT a.gaps
                FROM assessments a
                WHERE a.user_id = u.id
                ORDER BY a.id DESC
                LIMIT 1
            ) AS latest_gaps,

            (
                SELECT COUNT(*)
                FROM assessments a
                WHERE a.user_id = u.id
            ) AS assessment_count,

            (
                SELECT COUNT(*)
                FROM quiz_results q
                WHERE q.user_id = u.id
            ) AS material_quiz_count,

            (
                SELECT COUNT(*)
                FROM adaptive_quiz_results aq
                WHERE aq.user_id = u.id
            ) AS adaptive_quiz_count,

            (
                SELECT AVG(q.score * 100.0 / q.total)
                FROM quiz_results q
                WHERE q.user_id = u.id AND q.total > 0
            ) AS material_average,

            (
                SELECT AVG(aq.score * 100.0 / aq.total)
                FROM adaptive_quiz_results aq
                WHERE aq.user_id = u.id AND aq.total > 0
            ) AS adaptive_average

        FROM users u
        WHERE u.role = 'learner'
        ORDER BY u.id DESC
    """).fetchall()

    conn.close()

    return render_template_string("""
    <html>
    <head>
        <title>Learner Progress</title>
    </head>
    <body>

        <h1>Learner Progress Tracking</h1>

        {% if learners %}

        <table border="1" cellpadding="8">

            <tr>
                <th>Learner Email</th>
                <th>Assessments</th>
                <th>Latest Skill Gaps</th>
                <th>Material Quizzes</th>
                <th>Material Average</th>
                <th>Adaptive Quizzes</th>
                <th>Adaptive Average</th>
            </tr>

            {% for learner in learners %}

            <tr>
                <td>{{ learner.email }}</td>
                <td>{{ learner.assessment_count }}</td>
                <td>{{ learner.latest_gaps or 'Not assessed yet' }}</td>
                <td>{{ learner.material_quiz_count }}</td>

                <td>
                    {% if learner.material_average is not none %}
                        {{ learner.material_average|round(1) }}%
                    {% else %}
                        N/A
                    {% endif %}
                </td>

                <td>{{ learner.adaptive_quiz_count }}</td>

                <td>
                    {% if learner.adaptive_average is not none %}
                        {{ learner.adaptive_average|round(1) }}%
                    {% else %}
                        N/A
                    {% endif %}
                </td>
            </tr>

            {% endfor %}

        </table>

        {% else %}

            <p>No learner accounts found.</p>

        {% endif %}

        <br>
        <a href="/admin-dashboard">Back to Admin Dashboard</a>

    </body>
    </html>
    """, learners=learners)


# ASSESSMENT

@app.route('/assessment', methods=['GET', 'POST'])
def assessment():

    if 'user_id' not in session or session['role'] != 'learner':
        return redirect(url_for('login'))

    if request.method == 'POST':

        python = request.form.get('python')
        data_analysis = request.form.get('data_analysis')
        machine_learning = request.form.get('machine_learning')
        statistics = request.form.get('statistics')

        skills = {
            "Python Programming": python,
            "Data Analysis": data_analysis,
            "Machine Learning": machine_learning,
            "Statistics": statistics
        }

        score_map = {
            "Beginner": 1,
            "Intermediate": 2,
            "Advanced": 3
        }

        gaps = []

        for skill, level in skills.items():

            if level not in score_map:
                return "Invalid skill level.", 400

            if score_map[level] < 3:
                gaps.append(skill)

        gaps_text = (
            ", ".join(gaps)
            if gaps
            else "No competency gaps identified"
        )

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO assessments
            (user_id, python, data_analysis, machine_learning, statistics, gaps)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session['user_id'],
            python,
            data_analysis,
            machine_learning,
            statistics,
            gaps_text
        ))

        conn.commit()
        conn.close()

        return render_template_string("""
        <h1>Assessment Results</h1>

        <h2>Your Skill Levels</h2>

        <ul>
        {% for skill, level in skills.items() %}
            <li>{{ skill }}: {{ level }}</li>
        {% endfor %}
        </ul>

        <h2>Competency Gaps</h2>

        {% if gaps %}
            <ul>
            {% for gap in gaps %}
                <li>{{ gap }}</li>
            {% endfor %}
            </ul>
        {% else %}
            <p>No competency gaps identified.</p>
        {% endif %}

        <a href="/recommendations">View Recommendations</a>
        <br><br>
        <a href="/learner-dashboard">Back to Dashboard</a>
        """, skills=skills, gaps=gaps)

    return render_template('assessment.html')

# RECOMMENDATIONS

@app.route('/recommendations')
def recommendations():

    if 'user_id' not in session or session['role'] != 'learner':
        return redirect(url_for('login'))

    conn = get_db_connection()

    data = conn.execute("""
        SELECT * FROM assessments
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (session['user_id'],)).fetchone()

    conn.close()

    if data is None:
        return "Complete your assessment first."

    catalogue = {
        "Python Programming": {
            "course": "Python Programming Fundamentals",
            "description": "Learn Python basics, variables, loops and functions.",
            "level": "Beginner"
        },
        "Data Analysis": {
            "course": "Data Analysis with Python",
            "description": "Learn data cleaning, analysis and visualization.",
            "level": "Intermediate"
        },
        "Machine Learning": {
            "course": "Introduction to Machine Learning",
            "description": "Learn machine learning concepts and basic models.",
            "level": "Beginner"
        },
        "Statistics": {
            "course": "Statistics for Data Science",
            "description": "Learn probability and statistical methods.",
            "level": "Intermediate"
        }
    }

    recommendations_list = []

    gaps = data['gaps'].split(", ")

    if gaps == ["No competency gaps identified"]:
        gaps = []

    for skill in gaps:

        if skill in catalogue:

            course = catalogue[skill].copy()
            course['skill'] = skill
            recommendations_list.append(course)

    return render_template(
        'recommendations.html',
        recommendations=recommendations_list
    )


# FILE VALIDATION

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# TEXT EXTRACTION

def extract_text(filepath, extension):

    text = ""

    if extension == "pdf":

        pdf = PdfReader(filepath)

        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    elif extension == "txt":

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

    elif extension == "docx":

        doc = Document(filepath)

        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " "
                text += "\n"

    elif extension == "pptx":

        presentation = Presentation(filepath)

        for slide in presentation.slides:

            for shape in slide.shapes:

                if hasattr(shape, "text"):
                    text += shape.text + "\n"

                if shape.has_table:

                    for row in shape.table.rows:

                        for cell in row.cells:
                            text += cell.text + " "

                        text += "\n"

    return text.strip()


# QUIZ GENERATION

def generate_questions(text, count=5):

    sentences = re.split(r'(?<=[.!?])\s+', text)

    stop_words = {
        "this", "that", "with", "from", "have", "which",
        "their", "there", "these", "those", "about",
        "would", "could", "should", "where", "when",
        "what", "while", "into", "also", "than",
        "then", "them", "they", "your", "will",
        "been", "being", "such", "some", "more",
        "most", "only", "each", "very", "because",
        "through", "using", "used", "uses", "over",
        "under", "after", "before", "between", "within",
        "other", "many", "much", "make", "made",
        "like", "just", "both", "must", "does",
        "doing", "done", "shall", "part", "information"
    }

    word_list = re.findall(
        r'\b[A-Za-z][A-Za-z0-9_-]{3,}\b',
        text
    )

    word_pool = list(set(
        word for word in word_list
        if word.lower() not in stop_words
    ))

    questions = []
    used_answers = set()

    random.shuffle(sentences)

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence.split()) < 7:
            continue

        words = re.findall(
            r'\b[A-Za-z][A-Za-z0-9_-]{3,}\b',
            sentence
        )

        candidates = [
            word for word in words
            if word.lower() not in stop_words
            and word.lower() not in used_answers
        ]

        if not candidates:
            continue

        answer = random.choice(candidates)

        distractors = list(set(
            word for word in word_pool
            if word.lower() != answer.lower()
        ))

        if len(distractors) < 3:
            continue

        distractors = random.sample(distractors, 3)

        options = distractors + [answer]

        random.shuffle(options)

        blank_sentence = re.sub(
            r'\b' + re.escape(answer) + r'\b',
            "________",
            sentence,
            count=1
        )

        questions.append({
            "question": blank_sentence,
            "options": options,
            "answer": answer
        })

        used_answers.add(answer.lower())

        if len(questions) >= count:
            break

    return questions


# UPLOAD MATERIAL

@app.route('/upload-material', methods=['GET', 'POST'])
def upload_material():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session['role'] not in ['trainer', 'admin']:
        return "Only trainers and admins can upload materials.", 403

    if request.method == 'POST':

        file = request.files.get('material')

        if file is None or file.filename == "":
            return "Please select a file."

        if not allowed_file(file.filename):
            return "Upload PDF, TXT, DOCX or PPTX files only."

        original_name = secure_filename(file.filename)

        extension = original_name.rsplit(".", 1)[1].lower()

        stored_name = str(uuid.uuid4()) + "." + extension

        filepath = os.path.join("uploads", stored_name)

        file.save(filepath)

        try:
            text = extract_text(filepath, extension)

        except Exception:
            if os.path.exists(filepath):
                os.remove(filepath)

            return "Error reading file. Please check your file format."

        if not text.strip():
            return "No readable text found in this document."

        conn = get_db_connection()

        cursor = conn.execute("""
            INSERT INTO materials
            (file_name, stored_name, extracted_text, uploaded_by)
            VALUES (?, ?, ?, ?)
        """, (
            original_name,
            stored_name,
            text,
            session['user_id']
        ))

        material_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return redirect(url_for('materials'))

    return render_template('upload_material.html')


# MATERIALS PAGE

@app.route('/materials')
def materials():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()

    files = conn.execute("""
        SELECT id, file_name, created_at
        FROM materials
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Learning Materials</title>
    </head>
    <body>

        <h1>Available Learning Materials</h1>

        {% if files %}

            {% for file in files %}

                <hr>

                <h3>{{ file.file_name }}</h3>

                <p>Uploaded: {{ file.created_at }}</p>

                {% if role == 'learner' %}
                    <a href="/quiz/{{ file.id }}">Start Quiz</a>
                {% else %}
                    <p>Uploaded learning material</p>
                {% endif %}

            {% endfor %}

        {% else %}

            <p>No materials uploaded yet.</p>

        {% endif %}

        <br><br>

        {% if role in ['trainer', 'admin'] %}
            <a href="/upload-material">Upload New Material</a>
            <br><br>
        {% endif %}

        {% if role == 'learner' %}
            <a href="/learner-dashboard">Back to Dashboard</a>
        {% elif role == 'trainer' %}
            <a href="/trainer-dashboard">Back to Dashboard</a>
        {% else %}
            <a href="/admin-dashboard">Back to Dashboard</a>
        {% endif %}

    </body>
    </html>
    """, files=files, role=session['role'])


# LEARNER QUIZ

@app.route('/quiz/<int:material_id>')
def take_quiz(material_id):

    if 'user_id' not in session or session['role'] != 'learner':
        return redirect(url_for('login'))

    conn = get_db_connection()

    material = conn.execute("""
        SELECT * FROM materials WHERE id = ?
    """, (material_id,)).fetchone()

    conn.close()

    if material is None:
        return "Material not found."

    questions = generate_questions(material['extracted_text'])

    if not questions:
        return "Could not generate quiz from this document. Try another material."

    session['quiz_questions'] = questions
    session['quiz_material_id'] = material_id
    session['quiz_file_name'] = material['file_name']

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AEOLP Quiz</title>
    </head>
    <body>

        <h1>Learning Material Quiz</h1>

        <h2>{{ filename }}</h2>

        <form method="POST" action="/quiz-submit">

            {% for q in questions %}

                {% set q_index = loop.index0 %}

                <hr>

                <h3>Question {{ loop.index }}</h3>

                <p>{{ q.question }}</p>

                {% for option in q.options %}

                    <input type="radio"
                           name="q{{ q_index }}"
                           value="{{ option }}"
                           required>

                    {{ option }}

                    <br>

                {% endfor %}

            {% endfor %}

            <br><br>

            <button type="submit">Submit Quiz</button>

        </form>

        <br>

        <a href="/materials">Back to Materials</a>

    </body>
    </html>
    """, questions=questions, filename=material['file_name'])


# QUIZ SUBMISSION

@app.route('/quiz-submit', methods=['POST'])
def quiz_submit():

    if 'user_id' not in session or session['role'] != 'learner':
        return redirect(url_for('login'))

    questions = session.get('quiz_questions')

    if not questions:
        return "Quiz session expired. Please start the quiz again."

    score = 0
    total = len(questions)
    results = []

    for index, question in enumerate(questions):

        selected = request.form.get(f'q{index}')
        correct = question['answer']

        is_correct = selected == correct

        if is_correct:
            score += 1

        results.append({
            "question": question['question'],
            "selected": selected,
            "correct": correct,
            "is_correct": is_correct
        })

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO quiz_results
        (user_id, file_name, score, total)
        VALUES (?, ?, ?, ?)
    """, (
        session['user_id'],
        session.get('quiz_file_name', 'Learning Material'),
        score,
        total
    ))

    conn.commit()
    conn.close()

    session.pop('quiz_questions', None)

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Quiz Result</title>
    </head>
    <body>

        <h1>Quiz Completed!</h1>

        <h2>Your Score: {{ score }} / {{ total }}</h2>

        {% for item in results %}

            <hr>

            <h3>Question {{ loop.index }}</h3>

            <p>{{ item.question }}</p>

            <p>Your Answer: {{ item.selected or 'Not answered' }}</p>

            <p>Correct Answer: {{ item.correct }}</p>

            {% if item.is_correct %}
                <p>Correct!</p>
            {% else %}
                <p>Incorrect</p>
            {% endif %}

        {% endfor %}

        <br>

        <a href="/materials">Try Another Quiz</a>

        <br><br>

        <a href="/quiz-history">View Quiz History</a>

        <br><br>

        <a href="/learner-dashboard">Back to Dashboard</a>

    </body>
    </html>
    """, score=score, total=total, results=results)


# QUIZ HISTORY

@app.route('/quiz-history')
def quiz_history():

    if 'user_id' not in session or session['role'] != 'learner':
        return redirect(url_for('login'))

    conn = get_db_connection()

    history = conn.execute("""
        SELECT file_name, score, total, created_at
        FROM quiz_results
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session['user_id'],)).fetchall()

    conn.close()

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Quiz History - AEOLP</title>
    </head>
    <body>

        <h1>My Quiz History</h1>

        {% if history %}

            <table border="1" cellpadding="10">
                <tr>
                    <th>Learning Material</th>
                    <th>Score</th>
                    <th>Percentage</th>
                    <th>Date</th>
                </tr>

                {% for quiz in history %}
                <tr>
                    <td>{{ quiz.file_name }}</td>
                    <td>{{ quiz.score }} / {{ quiz.total }}</td>
                    <td>
                        {% if quiz.total and quiz.total > 0 %}
                            {{ ((quiz.score / quiz.total) * 100)|round(1) }}%
                        {% else %}
                            N/A
                        {% endif %}
                    </td>
                    <td>{{ quiz.created_at }}</td>
                </tr>
                {% endfor %}
            </table>

        {% else %}

            <p>You have not completed any quizzes yet.</p>

        {% endif %}

        <br>

        <a href="/materials">Take Another Quiz</a>

        <br><br>

        <a href="/learner-dashboard">Back to Dashboard</a>

    </body>
    </html>
    """, history=history)

# SMART ADAPTIVE QUIZ

@app.route('/adaptive-quiz', methods=['GET', 'POST'])
def adaptive_quiz():

    if 'user_id' not in session or session.get('role') != 'learner':
        return redirect(url_for('login'))

    if request.method == 'POST':

        topic = request.form.get('topic', '')

        if topic not in QUESTION_BANK:
            return 'Invalid topic selected.', 400

        conn = get_db_connection()

        previous = conn.execute(
            """
            SELECT score, total
            FROM adaptive_quiz_results
            WHERE user_id = ? AND topic = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (session['user_id'], topic)
        ).fetchone()

        conn.close()

        if previous is None:
            target_difficulty = 'Easy'

        else:

            percentage = (
                previous['score'] / previous['total'] * 100
            ) if previous['total'] else 0

            if percentage >= 80:
                target_difficulty = 'Hard'

            elif percentage >= 50:
                target_difficulty = 'Medium'

            else:
                target_difficulty = 'Easy'

        topic_questions = QUESTION_BANK[topic]

        priority = {
            'Easy': ['Easy', 'Medium', 'Hard'],
            'Medium': ['Medium', 'Easy', 'Hard'],
            'Hard': ['Hard', 'Medium', 'Easy']
        }[target_difficulty]

        chosen = []

        for level in priority:

            candidates = [
                q for q in topic_questions
                if q['difficulty'] == level and q not in chosen
            ]

            random.shuffle(candidates)

            for q in candidates:

                if len(chosen) >= 3:
                    break

                chosen.append(q)

            if len(chosen) >= 3:
                break

        random.shuffle(chosen)

        quiz_items = []

        for q in chosen:

            correct_index = ord(q['answer'].upper()) - ord('A')

            correct_text = q['options'][correct_index]

            options = list(q['options'])

            random.shuffle(options)

            quiz_items.append({
                'question': q['question'],
                'options': options,
                'answer': correct_text,
                'explanation': q.get('explanation', ''),
                'difficulty': q['difficulty']
            })

        session['adaptive_questions'] = quiz_items
        session['adaptive_topic'] = topic
        session['adaptive_target_difficulty'] = target_difficulty

        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AEOLP Adaptive Quiz</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">

            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 850px;
                    margin: 30px auto;
                    padding: 20px;
                    background: #f5f7fb;
                    color: #222;
                }

                .card {
                    background: white;
                    padding: 20px;
                    margin: 16px 0;
                    border-radius: 12px;
                }

                button {
                    padding: 10px 18px;
                    background: #2457a7;
                    color: white;
                    border: 0;
                    border-radius: 7px;
                    cursor: pointer;
                }
            </style>
        </head>

        <body>

            <h1>Smart Adaptive Quiz</h1>

            <p>
                Topic: <b>{{ topic }}</b> |
                Target difficulty: <b>{{ level }}</b>
            </p>

            <form method="POST" action="/adaptive-quiz/submit">

                {% for q in questions %}

                    {% set q_index = loop.index0 %}

                    <div class="card">

                        <h3>
                            Question {{ loop.index }}
                            <small>({{ q.difficulty }})</small>
                        </h3>

                        <p>{{ q.question }}</p>

                        {% for option in q.options %}

                            <label>
                                <input
                                    type="radio"
                                    name="q{{ q_index }}"
                                    value="{{ option }}"
                                    required
                                >

                                {{ option }}
                            </label>

                            <br>

                        {% endfor %}

                    </div>

                {% endfor %}

                <button type="submit">Submit Quiz</button>

            </form>

            <p>
                <a href="/learner-dashboard">Back to Dashboard</a>
            </p>

        </body>
        </html>
        """, topic=topic, level=target_difficulty, questions=quiz_items)

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Choose Adaptive Quiz</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 700px;
                margin: 40px auto;
                padding: 20px;
                background: #f5f7fb;
            }

            form {
                background: white;
                padding: 24px;
                border-radius: 12px;
            }

            select, button {
                padding: 10px;
                margin-top: 12px;
                width: 100%;
            }

            button {
                background: #2457a7;
                color: white;
                border: 0;
                border-radius: 7px;
                cursor: pointer;
            }
        </style>
    </head>

    <body>

        <h1>Smart Adaptive Quiz</h1>

        <p>
            Previous score batti next quiz difficulty
            automatic ga adjust avutundi.
        </p>

        <form method="POST">

            <label>Select topic:</label>

            <select name="topic" required>

                {% for topic in topics %}
                    <option value="{{ topic }}">{{ topic }}</option>
                {% endfor %}

            </select>

            <button type="submit">Start Quiz</button>

        </form>

        <p>
            <a href="/learner-dashboard">Back to Dashboard</a>
        </p>

    </body>
    </html>
    """, topics=list(QUESTION_BANK.keys()))


# ADAPTIVE QUIZ SUBMISSION

@app.route('/adaptive-quiz/submit', methods=['POST'])
def adaptive_quiz_submit():

    if 'user_id' not in session or session.get('role') != 'learner':
        return redirect(url_for('login'))

    questions = session.get('adaptive_questions')

    topic = session.get('adaptive_topic')

    if not questions or not topic:
        return redirect(url_for('adaptive_quiz'))

    score = 0

    results = []

    for i, q in enumerate(questions):

        selected = request.form.get(f'q{i}')

        correct = q['answer']

        is_correct = selected == correct

        score += int(is_correct)

        results.append({
            'question': q['question'],
            'selected': selected or 'Not answered',
            'correct': correct,
            'explanation': q['explanation'],
            'is_correct': is_correct
        })

    total = len(questions)

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO adaptive_quiz_results
        (user_id, topic, score, total, difficulty)
        VALUES (?, ?, ?, ?, ?)
    """, (
        session['user_id'],
        topic,
        score,
        total,
        session.get('adaptive_target_difficulty', 'Easy')
    ))

    conn.commit()
    conn.close()

    session.pop('adaptive_questions', None)
    session.pop('adaptive_topic', None)
    session.pop('adaptive_target_difficulty', None)

    percentage = round(score / total * 100) if total else 0

    if percentage >= 80:

        next_level = 'Hard'

        message = 'Excellent! Next quiz difficulty will increase to Hard.'

    elif percentage >= 50:

        next_level = 'Medium'

        message = 'Good progress. Next quiz difficulty will be Medium.'

    else:

        next_level = 'Easy'

        message = 'Practice a little more. Next quiz difficulty will be Easy.'

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Adaptive Quiz Result</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 850px;
                margin: 30px auto;
                padding: 20px;
                background: #f5f7fb;
                color: #222;
            }

            .card {
                background: white;
                padding: 20px;
                margin: 14px 0;
                border-radius: 12px;
            }
        </style>
    </head>

    <body>

        <h1>Quiz Results</h1>

        <h2>{{ score }} / {{ total }} ({{ percentage }}%)</h2>

        <p>{{ message }}</p>

        <p>
            Next target level:
            <b>{{ next_level }}</b>
        </p>

        {% for item in results %}

            <div class="card">

                <h3>Question {{ loop.index }}</h3>

                <p>{{ item.question }}</p>

                <p>Your answer: {{ item.selected }}</p>

                <p>
                    Correct answer:
                    <b>{{ item.correct }}</b>
                </p>

                <p>
                    {% if item.is_correct %}
                        Correct!
                    {% else %}
                        Incorrect.
                    {% endif %}
                </p>

                <p>Explanation: {{ item.explanation }}</p>

            </div>

        {% endfor %}

        <p>
            <a href="/adaptive-quiz">Take another adaptive quiz</a>
        </p>

        <p>
            <a href="/learner-dashboard">Dashboard</a>
        </p>

    </body>
    </html>
    """,
    score=score,
    total=total,
    percentage=percentage,
    message=message,
    next_level=next_level,
    results=results)


# ADAPTIVE QUIZ HISTORY

@app.route('/adaptive-quiz-history')
def adaptive_quiz_history():

    if 'user_id' not in session or session.get('role') != 'learner':
        return redirect(url_for('login'))

    conn = get_db_connection()

    history = conn.execute("""
        SELECT topic, score, total, difficulty, created_at
        FROM adaptive_quiz_results
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session['user_id'],)).fetchall()

    conn.close()

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Adaptive Quiz History</title>
    </head>
    <body>

        <h1>Adaptive Quiz History</h1>

        {% if history %}

            <table border="1" cellpadding="8">

                <tr>
                    <th>Topic</th>
                    <th>Score</th>
                    <th>Difficulty</th>
                    <th>Date</th>
                </tr>

                {% for h in history %}

                    <tr>
                        <td>{{ h.topic }}</td>

                        <td>
                            {{ h.score }}/{{ h.total }}
                            ({{ ((h.score/h.total)*100)|round(0) }}%)
                        </td>

                        <td>{{ h.difficulty }}</td>

                        <td>{{ h.created_at }}</td>
                    </tr>

                {% endfor %}

            </table>

        {% else %}

            <p>No adaptive quiz attempts yet.</p>

        {% endif %}

        <p>
            <a href="/adaptive-quiz">Start quiz</a>
        </p>

        <p>
            <a href="/learner-dashboard">Dashboard</a>
        </p>

    </body>
    </html>
    """, history=history)


# LOGOUT

@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))


# FILE SIZE ERROR

@app.errorhandler(413)
def file_too_large(error):

    return "File too large. Maximum upload size is 16 MB.", 413


# RUN APPLICATION

if __name__ == '__main__':

    initialize_database()

    app.run(debug=True)
