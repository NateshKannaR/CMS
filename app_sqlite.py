from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_db():
    conn = sqlite3.connect('cms.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        full_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Courses table
    c.execute('''CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        teacher_id INTEGER,
        course_code TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (teacher_id) REFERENCES users (id)
    )''')
    
    # Enrollments table
    c.execute('''CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users (id),
        FOREIGN KEY (course_id) REFERENCES courses (id)
    )''')
    
    # Assignments table
    c.execute('''CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        course_id INTEGER,
        due_date TIMESTAMP,
        max_points INTEGER DEFAULT 100,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses (id)
    )''')
    
    # Submissions table
    c.execute('''CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assignment_id INTEGER,
        student_id INTEGER,
        content TEXT,
        file_path TEXT,
        grade INTEGER,
        feedback TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (assignment_id) REFERENCES assignments (id),
        FOREIGN KEY (student_id) REFERENCES users (id)
    )''')
    
    # Messages table
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        sender_id INTEGER,
        content TEXT NOT NULL,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses (id),
        FOREIGN KEY (sender_id) REFERENCES users (id)
    )''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('cms.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[4]
            session['full_name'] = user[5]
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        full_name = request.form['full_name']
        
        hashed_password = generate_password_hash(password)
        
        conn = sqlite3.connect('cms.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, email, password, role, full_name) VALUES (?, ?, ?, ?, ?)',
                     (username, email, hashed_password, role, full_name))
            conn.commit()
            flash('Registration successful')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('cms.db')
    c = conn.cursor()
    
    if session['role'] == 'teacher':
        c.execute('SELECT * FROM courses WHERE teacher_id = ?', (session['user_id'],))
        courses = c.fetchall()
    else:
        c.execute('''SELECT c.* FROM courses c 
                     JOIN enrollments e ON c.id = e.course_id 
                     WHERE e.student_id = ?''', (session['user_id'],))
        courses = c.fetchall()
    
    conn.close()
    return render_template('dashboard_sqlite.html', courses=courses)

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('cms.db')
    c = conn.cursor()
    
    # Get course details
    c.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = c.fetchone()
    
    # Get assignments
    c.execute('SELECT * FROM assignments WHERE course_id = ? ORDER BY due_date', (course_id,))
    assignments = c.fetchall()
    
    # Get messages
    c.execute('''SELECT m.*, u.full_name FROM messages m 
                 JOIN users u ON m.sender_id = u.id 
                 WHERE m.course_id = ? ORDER BY m.sent_at DESC''', (course_id,))
    messages = c.fetchall()
    
    conn.close()
    return render_template('course_detail_sqlite.html', course=course, assignments=assignments, messages=messages)

@app.route('/create_course', methods=['GET', 'POST'])
def create_course():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        course_code = request.form['course_code']
        
        conn = sqlite3.connect('cms.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO courses (name, description, teacher_id, course_code) VALUES (?, ?, ?, ?)',
                     (name, description, session['user_id'], course_code))
            conn.commit()
            flash('Course created successfully')
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            flash('Course code already exists')
        finally:
            conn.close()
    
    return render_template('create_course.html')

@app.route('/join_course', methods=['POST'])
def join_course():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('dashboard'))
    
    course_code = request.form['course_code']
    
    conn = sqlite3.connect('cms.db')
    c = conn.cursor()
    
    # Find course by code
    c.execute('SELECT id FROM courses WHERE course_code = ?', (course_code,))
    course = c.fetchone()
    
    if course:
        try:
            c.execute('INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)',
                     (session['user_id'], course[0]))
            conn.commit()
            flash('Successfully joined course')
        except sqlite3.IntegrityError:
            flash('Already enrolled in this course')
    else:
        flash('Course not found')
    
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/create_assignment/<int:course_id>', methods=['GET', 'POST'])
def create_assignment(course_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        max_points = request.form['max_points']
        
        conn = sqlite3.connect('cms.db')
        c = conn.cursor()
        c.execute('INSERT INTO assignments (title, description, course_id, due_date, max_points) VALUES (?, ?, ?, ?, ?)',
                 (title, description, course_id, due_date, max_points))
        conn.commit()
        conn.close()
        
        flash('Assignment created successfully')
        return redirect(url_for('course_detail', course_id=course_id))
    
    return render_template('create_assignment.html', course_id=course_id)

@app.route('/assignment/<int:assignment_id>')
def assignment_detail(assignment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('cms.db')
    c = conn.cursor()
    
    # Get assignment details
    c.execute('SELECT * FROM assignments WHERE id = ?', (assignment_id,))
    assignment = c.fetchone()
    
    # Get user's submission if exists
    c.execute('SELECT * FROM submissions WHERE assignment_id = ? AND student_id = ?',
             (assignment_id, session['user_id']))
    submission = c.fetchone()
    
    # If teacher, get all submissions
    submissions = []
    if session['role'] == 'teacher':
        c.execute('''SELECT s.*, u.full_name FROM submissions s 
                     JOIN users u ON s.student_id = u.id 
                     WHERE s.assignment_id = ?''', (assignment_id,))
        submissions = c.fetchall()
    
    conn.close()
    return render_template('assignment_detail_sqlite.html', assignment=assignment, submission=submission, submissions=submissions)

@app.route('/submit_assignment/<int:assignment_id>', methods=['POST'])
def submit_assignment(assignment_id):
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('dashboard'))
    
    content = request.form['content']
    file_path = None
    
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
            file.save(file_path)
    
    conn = sqlite3.connect('cms.db')
    c = conn.cursor()
    
    # Check if submission already exists
    c.execute('SELECT id FROM submissions WHERE assignment_id = ? AND student_id = ?',
             (assignment_id, session['user_id']))
    existing = c.fetchone()
    
    if existing:
        c.execute('UPDATE submissions SET content = ?, file_path = ?, submitted_at = CURRENT_TIMESTAMP WHERE id = ?',
                 (content, file_path, existing[0]))
    else:
        c.execute('INSERT INTO submissions (assignment_id, student_id, content, file_path) VALUES (?, ?, ?, ?)',
                 (assignment_id, session['user_id'], content, file_path))
    
    conn.commit()
    conn.close()
    
    flash('Assignment submitted successfully')
    return redirect(url_for('assignment_detail', assignment_id=assignment_id))

@app.route('/grade_submission/<int:submission_id>', methods=['POST'])
def grade_submission(submission_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    grade = request.form['grade']
    feedback = request.form['feedback']
    
    conn = sqlite3.connect('cms.db')
    c = conn.cursor()
    c.execute('UPDATE submissions SET grade = ?, feedback = ? WHERE id = ?',
             (grade, feedback, submission_id))
    conn.commit()
    conn.close()
    
    flash('Grade submitted successfully')
    return redirect(request.referrer)

@app.route('/send_message/<int:course_id>', methods=['POST'])
def send_message(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    content = request.form['content']
    
    conn = sqlite3.connect('cms.db')
    c = conn.cursor()
    c.execute('INSERT INTO messages (course_id, sender_id, content) VALUES (?, ?, ?)',
             (course_id, session['user_id'], content))
    conn.commit()
    conn.close()
    
    return redirect(url_for('course_detail', course_id=course_id))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)