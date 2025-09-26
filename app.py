from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from datetime import datetime, timedelta
import uuid
import re

# Input validation functions
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    return len(username) >= 3 and username.isalnum()

def validate_password(password):
    return len(password) >= 6

def validate_course_code(code):
    return len(code) >= 3 and len(code) <= 10 and code.replace('-', '').replace('_', '').isalnum()

def sanitize_input(text):
    if not text:
        return ''
    return text.strip()[:500]  # Limit length and strip whitespace

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.permanent_session_lifetime = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Disable caching for development
@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# MongoDB connection (Atlas)
try:
    print('Connecting to MongoDB Atlas...')
    mongo_uri = os.environ.get('MONGODB_URI', 'mongodb+srv://Natesh:Natesh1974@cluster0.wwp3oig.mongodb.net/')
    client = MongoClient(mongo_uri)
    db = client.cms_database
    client.admin.command('ping')
    print('SUCCESS: MongoDB Atlas connected successfully!')
except Exception as e:
    print(f'ERROR: MongoDB connection failed: {e}')
    client = None
    db = None

def init_db():
    if db is None:
        print('MongoDB not connected, skipping initialization')
        return
    try:
        db.users.create_index([('username', 1)], unique=True)
        db.users.create_index([('email', 1)], unique=True)
        db.courses.create_index([('course_code', 1)], unique=True)
        print('MongoDB collections initialized')
    except Exception as e:
        print(f'Error initializing MongoDB: {e}')

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        if db is None:
            flash('Database connection error')
            return render_template('login.html')
            
        username = request.form['username']
        password = request.form['password']
        
        try:
            user = db.users.find_one({'username': username})
            
            if user and check_password_hash(user['password'], password):
                if user['role'] != 'student':
                    flash('Invalid student credentials')
                    return render_template('login.html')
                elif user.get('status') == 'rejected':
                    flash('Your account has been rejected. Please contact admin.')
                    return render_template('login.html')
                else:
                    session.permanent = True
                    session['user_id'] = str(user['_id'])
                    session['username'] = user['username']
                    session['role'] = user['role']
                    session['full_name'] = user['full_name']
                    return redirect(url_for('dashboard'))
            else:
                flash('Invalid student credentials')
        except Exception as e:
            flash(f'Database error: {str(e)}')
    
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if db is None:
            flash('Database connection error')
            return render_template('login.html')
            
        username = request.form['username']
        password = request.form['password']
        
        try:
            user = db.users.find_one({'username': username})
            
            if user and check_password_hash(user['password'], password):
                if user['role'] != 'student':
                    flash('Invalid student credentials')
                    return render_template('login.html')
                elif user.get('status') == 'rejected':
                    flash('Your account has been rejected. Please contact admin.')
                    return render_template('login.html')
                else:
                    session['user_id'] = str(user['_id'])
                    session['username'] = user['username']
                    session['role'] = user['role']
                    session['full_name'] = user['full_name']
                    return redirect(url_for('dashboard'))
            else:
                flash('Invalid student credentials')
        except Exception as e:
            flash(f'Database error: {str(e)}')
    
    return render_template('login.html')

@app.route('/tutor_login', methods=['GET', 'POST'])
def tutor_login():
    if request.method == 'POST':
        if db is None:
            flash('Database connection error')
            return render_template('tutor_login.html')
            
        username = request.form['username']
        password = request.form['password']
        
        try:
            user = db.users.find_one({'username': username, 'role': 'teacher'})
            
            if user and check_password_hash(user['password'], password):
                if user.get('status') == 'pending':
                    flash('Your teacher account is pending admin approval. Please wait for confirmation.')
                    return render_template('tutor_login.html')
                elif user.get('status') == 'rejected':
                    flash('Your account has been rejected. Please contact admin.')
                    return render_template('tutor_login.html')
                else:
                    session.permanent = True
                    session['user_id'] = str(user['_id'])
                    session['username'] = user['username']
                    session['role'] = user['role']
                    session['full_name'] = user['full_name']
                    return redirect(url_for('dashboard'))
            else:
                flash('Invalid tutor credentials')
        except Exception as e:
            flash(f'Database error: {str(e)}')
    
    return render_template('tutor_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if db is None:
            flash('Database connection error. Please try again later.')
            return render_template('register.html')
            
        username = sanitize_input(request.form.get('username', ''))
        email = sanitize_input(request.form.get('email', ''))
        password = request.form.get('password', '')
        role = request.form.get('role', '')
        full_name = sanitize_input(request.form.get('full_name', ''))
        
        # Input validation
        if not validate_username(username):
            flash('Username must be at least 3 characters and contain only letters and numbers')
            return render_template('register.html')
        
        if not validate_email(email):
            flash('Please enter a valid email address')
            return render_template('register.html')
        
        if not validate_password(password):
            flash('Password must be at least 6 characters long')
            return render_template('register.html')
        
        if role not in ['student', 'teacher']:
            flash('Invalid role selected')
            return render_template('register.html')
        
        if not full_name or len(full_name) < 2:
            flash('Full name must be at least 2 characters long')
            return render_template('register.html')
        
        try:
            if db.users.find_one({'$or': [{'username': username}, {'email': email}]}):
                flash('Username or email already exists')
            else:
                hashed_password = generate_password_hash(password)
                user_data = {
                    'username': username,
                    'email': email,
                    'password': hashed_password,
                    'role': role,
                    'full_name': full_name,
                    'created_at': datetime.now()
                }
                
                if role == 'teacher':
                    user_data['status'] = 'pending'
                    flash('Registration successful! Please wait for admin approval.')
                else:
                    user_data['status'] = 'approved'
                    flash('Registration successful!')
                
                db.users.insert_one(user_data)
                return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed. Please try again.')
            print(f'Registration error: {e}')
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if db is None:
        flash('Database connection error')
        return render_template('dashboard.html', courses=[], user_email='', user_joined_date='', user_photo='')
    
    try:
        user = db.users.find_one({'_id': ObjectId(session['user_id'])})
        user_email = user.get('email', '') if user else ''
        user_joined_date = user.get('created_at').strftime('%Y-%m-%d') if user and user.get('created_at') else ''
        user_photo = user.get('profile_photo', '') if user else ''
        
        if session['role'] == 'teacher':
            courses = list(db.courses.find({'teacher_id': ObjectId(session['user_id'])}))
        else:
            enrollments = db.enrollments.find({'student_id': ObjectId(session['user_id'])})
            course_ids = [e['course_id'] for e in enrollments]
            courses = list(db.courses.find({'_id': {'$in': course_ids}}))
        
        return render_template('dashboard.html', courses=courses, user_email=user_email, user_joined_date=user_joined_date, user_photo=user_photo)
    except Exception as e:
        flash(f'Error loading courses: {str(e)}')
        return render_template('dashboard.html', courses=[], user_email='', user_joined_date='', user_photo='')

@app.route('/calendar')
def calendar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if db is None:
        return render_template('calendar.html', assignments=[], courses={})
    
    try:
        if session['role'] == 'teacher':
            courses = list(db.courses.find({'teacher_id': ObjectId(session['user_id'])}))
            course_ids = [c['_id'] for c in courses]
            assignments = list(db.assignments.find({'course_id': {'$in': course_ids}}))
        else:
            enrollments = db.enrollments.find({'student_id': ObjectId(session['user_id'])})
            course_ids = [e['course_id'] for e in enrollments]
            assignments = list(db.assignments.find({'course_id': {'$in': course_ids}}))
        
        courses_dict = {c['_id']: c['name'] for c in db.courses.find({'_id': {'$in': course_ids}})}
        return render_template('calendar.html', assignments=assignments, courses=courses_dict)
    except Exception as e:
        return render_template('calendar.html', assignments=[], courses={})



@app.route('/course/<course_id>')
def course_detail(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if db is None:
        flash('Database connection error')
        return redirect(url_for('dashboard'))
    
    try:
        course = db.courses.find_one({'_id': ObjectId(course_id)})
        if not course:
            flash('Course not found')
            return redirect(url_for('dashboard'))
        
        teacher = db.users.find_one({'_id': course['teacher_id']})
        teacher_name = teacher['full_name'] if teacher else 'Unknown'
        
        enrollments = list(db.enrollments.find({'course_id': ObjectId(course_id)}))
        assignments = list(db.assignments.find({'course_id': ObjectId(course_id)}).sort('due_date', 1))
        materials = list(db.materials.find({'course_id': ObjectId(course_id)}).sort('uploaded_at', -1))
        announcements = []
        
        return render_template('course_detail.html', 
                             course=course, 
                             assignments=assignments, 
                             materials=materials, 
                             enrollments=enrollments,
                             announcements=announcements,
                             teacher_name=teacher_name)
    except Exception as e:
        flash(f'Error loading course: {str(e)}')
        return redirect(url_for('dashboard'))

@app.route('/create_course', methods=['GET', 'POST'])
def create_course():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            name = sanitize_input(request.form.get('name', ''))
            description = sanitize_input(request.form.get('description', ''))
            course_code = sanitize_input(request.form.get('course_code', '')).upper()
            
            # Input validation
            if not name or len(name) < 3:
                flash('Course name must be at least 3 characters long')
                return render_template('create_course.html')
            
            if not validate_course_code(course_code):
                flash('Course code must be 3-10 characters, letters and numbers only')
                return render_template('create_course.html')
            
            if db.courses.find_one({'course_code': course_code}):
                flash('Course code already exists')
                return render_template('create_course.html')
            
            db.courses.insert_one({
                'name': name,
                'description': description,
                'teacher_id': ObjectId(session['user_id']),
                'course_code': course_code,
                'created_at': datetime.now()
            })
            flash('Course created successfully')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash('Failed to create course. Please try again.')
            print(f'Course creation error: {e}')
    
    return render_template('create_course.html')

@app.route('/join_course', methods=['POST'])
def join_course():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('dashboard'))
    
    try:
        course_code = sanitize_input(request.form.get('course_code', '')).upper()
        
        if not validate_course_code(course_code):
            flash('Invalid course code format')
            return redirect(url_for('dashboard'))
        
        course = db.courses.find_one({'course_code': course_code})
        
        if course:
            existing = db.enrollments.find_one({
                'student_id': ObjectId(session['user_id']),
                'course_id': course['_id']
            })
            
            if existing:
                flash('Already enrolled in this course')
            else:
                db.enrollments.insert_one({
                    'student_id': ObjectId(session['user_id']),
                    'course_id': course['_id'],
                    'enrolled_at': datetime.now()
                })
                flash('Successfully joined course')
        else:
            flash('Course not found')
            
    except Exception as e:
        flash('Failed to join course. Please try again.')
        print(f'Course join error: {e}')
    
    return redirect(url_for('dashboard'))

@app.route('/create_assignment/<course_id>', methods=['GET', 'POST'])
def create_assignment(course_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        max_points = int(request.form['max_points'])
        
        db.assignments.insert_one({
            'title': title,
            'description': description,
            'course_id': ObjectId(course_id),
            'due_date': due_date,
            'max_points': max_points,
            'created_at': datetime.now()
        })
        
        flash('Assignment created successfully')
        return redirect(url_for('course_detail', course_id=course_id))
    
    return render_template('create_assignment.html', course_id=course_id)

@app.route('/assignment/<assignment_id>')
def assignment_detail(assignment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    assignment = db.assignments.find_one({'_id': ObjectId(assignment_id)})
    
    submission = db.submissions.find_one({
        'assignment_id': ObjectId(assignment_id),
        'student_id': ObjectId(session['user_id'])
    })
    
    submissions = []
    if session['role'] == 'teacher':
        submissions = list(db.submissions.aggregate([
            {'$match': {'assignment_id': ObjectId(assignment_id)}},
            {'$lookup': {
                'from': 'users',
                'localField': 'student_id',
                'foreignField': '_id',
                'as': 'student'
            }}
        ]))
    
    return render_template('assignment_detail.html', assignment=assignment, submission=submission, submissions=submissions)

@app.route('/submit_assignment/<assignment_id>', methods=['POST'])
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
    
    existing = db.submissions.find_one({
        'assignment_id': ObjectId(assignment_id),
        'student_id': ObjectId(session['user_id'])
    })
    
    if existing:
        db.submissions.update_one(
            {'_id': existing['_id']},
            {'$set': {
                'content': content,
                'file_path': file_path,
                'submitted_at': datetime.now()
            }}
        )
    else:
        db.submissions.insert_one({
            'assignment_id': ObjectId(assignment_id),
            'student_id': ObjectId(session['user_id']),
            'content': content,
            'file_path': file_path,
            'submitted_at': datetime.now()
        })
    
    flash('Assignment submitted successfully')
    return redirect(url_for('assignment_detail', assignment_id=assignment_id))

@app.route('/grade_submission/<submission_id>', methods=['POST'])
def grade_submission(submission_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    grade = int(request.form['grade']) if request.form['grade'] else None
    feedback = request.form['feedback']
    
    db.submissions.update_one(
        {'_id': ObjectId(submission_id)},
        {'$set': {
            'grade': grade,
            'feedback': feedback
        }}
    )
    
    flash('Grade submitted successfully')
    return redirect(request.referrer)

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['username'] != 'admin':
        flash('Admin access required')
        return redirect(url_for('admin_login'))
    
    pending_teachers = list(db.users.find({'role': 'teacher', 'status': 'pending'}))
    return render_template('admin_dashboard.html', pending_teachers=pending_teachers)

@app.route('/admin/approve/<user_id>')
def approve_teacher(user_id):
    if 'user_id' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))
    
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'status': 'approved'}})
    flash('Teacher approved successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<user_id>')
def reject_teacher(user_id):
    if 'user_id' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))
    
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'status': 'rejected'}})
    flash('Teacher rejected')
    return redirect(url_for('admin_dashboard'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    full_name = request.form['full_name']
    email = request.form['email']
    
    update_data = {'full_name': full_name, 'email': email}
    
    if 'profile_photo' in request.files:
        file = request.files['profile_photo']
        if file.filename != '':
            filename = secure_filename(file.filename)
            photo_filename = f"{uuid.uuid4()}_{filename}"
            os.makedirs('static/uploads', exist_ok=True)
            file.save(os.path.join('static/uploads', photo_filename))
            update_data['profile_photo'] = photo_filename
    
    db.users.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': update_data}
    )
    
    session['full_name'] = full_name
    flash('Profile updated successfully')
    return redirect(url_for('dashboard'))

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    if new_password != confirm_password:
        flash('New passwords do not match')
        return redirect(url_for('dashboard'))
    
    user = db.users.find_one({'_id': ObjectId(session['user_id'])})
    
    if not check_password_hash(user['password'], current_password):
        flash('Current password is incorrect')
        return redirect(url_for('dashboard'))
    
    hashed_new_password = generate_password_hash(new_password)
    
    db.users.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {'password': hashed_new_password}}
    )
    
    flash('Password changed successfully')
    return redirect(url_for('dashboard'))

@app.route('/upload_material/<course_id>', methods=['POST'])
def upload_material(course_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    try:
        title = sanitize_input(request.form.get('title', ''))
        description = sanitize_input(request.form.get('description', ''))
        
        if not title or len(title) < 3:
            flash('Material title must be at least 3 characters long')
            return redirect(url_for('course_detail', course_id=course_id))
        
        file_path = None
        filename = None
        
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                # Validate file size (10MB limit)
                if len(file.read()) > 10 * 1024 * 1024:
                    flash('File size must be less than 10MB')
                    return redirect(url_for('course_detail', course_id=course_id))
                
                file.seek(0)  # Reset file pointer
                
                # Validate file type
                allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.ppt', '.pptx', '.jpg', '.png', '.zip'}
                file_ext = os.path.splitext(file.filename)[1].lower()
                
                if file_ext not in allowed_extensions:
                    flash('File type not allowed. Allowed types: PDF, DOC, DOCX, TXT, PPT, PPTX, JPG, PNG, ZIP')
                    return redirect(url_for('course_detail', course_id=course_id))
                
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
                file.save(file_path)
        
        db.materials.insert_one({
            'title': title,
            'description': description,
            'course_id': ObjectId(course_id),
            'file_path': file_path,
            'filename': filename,
            'uploaded_by': ObjectId(session['user_id']),
            'uploaded_at': datetime.now()
        })
        
        flash('Material uploaded successfully')
        
    except Exception as e:
        flash('Failed to upload material. Please try again.')
        print(f'Material upload error: {e}')
    
    return redirect(url_for('course_detail', course_id=course_id))

@app.route('/download_material/<material_id>')
def download_material(material_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    material = db.materials.find_one({'_id': ObjectId(material_id)})
    if material and material['file_path']:
        return send_file(material['file_path'], as_attachment=True, download_name=material['filename'])
    
    flash('File not found')
    return redirect(request.referrer)

@app.route('/whiteboard')
def whiteboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('whiteboard.html')

@app.route('/video_lectures')
def video_lectures():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('video_lectures.html')

@app.route('/attendance')
def attendance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('attendance.html')

@app.route('/notifications')
def get_notifications():
    if 'user_id' not in session:
        return {'notifications': []}
    
    if db is None:
        return {'notifications': []}
    
    try:
        query = {
            '$or': [
                {'target_role': session['role']},
                {'target_role': 'all'},
                {'target_user_id': ObjectId(session['user_id'])}
            ]
        }
        
        notifications = list(db.notifications.find(query).sort('created_at', -1).limit(10))
        
        return {
            'notifications': [{
                'message': n['message'],
                'sender': n.get('sender_name', 'System'),
                'created_at': n['created_at'].strftime('%Y-%m-%d %H:%M')
            } for n in notifications]
        }
    except Exception as e:
        return {'notifications': []}

@app.route('/chatbot', methods=['POST'])
def chatbot():
    if 'user_id' not in session or session['role'] != 'student':
        return {'response': 'Access denied'}, 403
    
    data = request.get_json()
    message = data.get('message', '').lower()
    
    if 'hello' in message or 'hi' in message:
        response = "Hello! I'm here to help you with your studies. What would you like to know?"
    elif 'assignment' in message:
        response = "For assignments, check your course dashboard. You can submit work, view due dates, and see grades there."
    elif 'course' in message:
        response = "To join a course, get the course code from your teacher and use the 'Join Course' option on your dashboard."
    elif 'grade' in message:
        response = "You can view your grades in the assignment details. Teachers will provide feedback along with grades."
    else:
        response = "I'm here to help! Try asking about courses, assignments, grades, or submissions."
    
    return {'response': response}

@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        max_participants = int(request.form['max_participants'])
        questions = []
        
        i = 0
        while f'question_{i}' in request.form:
            question = {
                'question': request.form[f'question_{i}'],
                'options': [
                    request.form[f'option_{i}_0'],
                    request.form[f'option_{i}_1'],
                    request.form[f'option_{i}_2'],
                    request.form[f'option_{i}_3']
                ],
                'correct_answer': int(request.form[f'correct_{i}'])
            }
            questions.append(question)
            i += 1
        
        quiz_code = str(uuid.uuid4())[:8].upper()
        
        db.quizzes.insert_one({
            'title': title,
            'quiz_code': quiz_code,
            'teacher_id': ObjectId(session['user_id']),
            'questions': questions,
            'max_participants': max_participants,
            'status': 'waiting',
            'current_question': 0,
            'participants': [],
            'created_at': datetime.now()
        })
        
        flash('Quiz created successfully')
        return redirect(url_for('dashboard'))
    
    return render_template('create_quiz.html')

@app.route('/join_quiz', methods=['GET', 'POST'])
def join_quiz():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        quiz_code = request.form['quiz_code'].upper()
        quiz = db.quizzes.find_one({'quiz_code': quiz_code})
        
        if not quiz:
            flash('Quiz not found')
            return render_template('join_quiz.html')
        
        if len(quiz['participants']) >= quiz['max_participants']:
            flash('Quiz is full')
            return render_template('join_quiz.html')
        
        db.quizzes.update_one(
            {'_id': quiz['_id']},
            {'$addToSet': {'participants': {
                'user_id': ObjectId(session['user_id']),
                'name': session['full_name'],
                'score': 0,
                'answers': []
            }}}
        )
        
        return redirect(url_for('quiz_room', quiz_id=quiz['_id']))
    
    return render_template('join_quiz.html')

@app.route('/quiz/<quiz_id>')
def quiz_room(quiz_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id)})
    return render_template('quiz_room.html', quiz=quiz)

@app.route('/practice_quiz')
def practice_quiz():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('dashboard'))
    
    quizzes = list(db.practice_quizzes.find()) if db is not None else []
    return render_template('practice_quiz_list.html', quizzes=quizzes)

@app.route('/take_practice_quiz/<quiz_id>')
def take_practice_quiz(quiz_id):
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('dashboard'))
    
    if db is None:
        flash('Database connection error')
        return redirect(url_for('practice_quiz'))
    
    try:
        quiz = db.practice_quizzes.find_one({'_id': ObjectId(quiz_id)})
        if not quiz:
            flash('Quiz not found')
            return redirect(url_for('practice_quiz'))
        
        return render_template('take_practice_quiz.html', quiz=quiz)
    except Exception as e:
        flash('Error loading quiz')
        return redirect(url_for('practice_quiz'))

@app.route('/search', methods=['POST'])
def search():
    if 'user_id' not in session or db is None:
        return {'results': []}
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if len(query) < 2:
            return {'results': []}
        
        results = []
        
        if session['role'] == 'teacher':
            courses = db.courses.find({
                'teacher_id': ObjectId(session['user_id']),
                '$or': [
                    {'name': {'$regex': query, '$options': 'i'}},
                    {'course_code': {'$regex': query, '$options': 'i'}}
                ]
            }).limit(5)
        else:
            enrollments = db.enrollments.find({'student_id': ObjectId(session['user_id'])})
            course_ids = [e['course_id'] for e in enrollments]
            courses = db.courses.find({
                '_id': {'$in': course_ids},
                '$or': [
                    {'name': {'$regex': query, '$options': 'i'}},
                    {'course_code': {'$regex': query, '$options': 'i'}}
                ]
            }).limit(5)
        
        for course in courses:
            results.append({
                'type': 'course',
                'title': course['name'],
                'description': f"Course Code: {course['course_code']}",
                'url': url_for('course_detail', course_id=course['_id'])
            })
        
        return {'results': results[:10]}
        
    except Exception as e:
        return {'results': []}

@app.route('/teacher_messages')
def teacher_messages():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    if db is None:
        return render_template('teacher_messages.html', conversations=[])
    
    try:
        teacher_courses = list(db.courses.find({'teacher_id': ObjectId(session['user_id'])}))
        course_ids = [c['_id'] for c in teacher_courses]
        
        pipeline = [
            {'$match': {
                'course_id': {'$in': course_ids},
                'recipient_id': ObjectId(session['user_id'])
            }},
            {'$sort': {'sent_at': -1}},
            {'$group': {
                '_id': '$sender_id',
                'latest_message': {'$first': '$$ROOT'}
            }},
            {'$lookup': {
                'from': 'users',
                'localField': '_id',
                'foreignField': '_id',
                'as': 'student'
            }},
            {'$lookup': {
                'from': 'courses',
                'localField': 'latest_message.course_id',
                'foreignField': '_id',
                'as': 'course'
            }}
        ]
        
        conversations = list(db.messages.aggregate(pipeline))
        return render_template('teacher_messages.html', conversations=conversations)
        
    except Exception as e:
        return render_template('teacher_messages.html', conversations=[])

@app.route('/get_messages/<course_id>')
def get_messages(course_id):
    if 'user_id' not in session:
        return {'messages': []}
    
    if db is None:
        return {'messages': []}
    
    try:
        course = db.courses.find_one({'_id': ObjectId(course_id)})
        if not course:
            return {'messages': []}
        
        if session['role'] == 'student':
            # Student can only see messages between them and the teacher
            messages = list(db.messages.find({
                'course_id': ObjectId(course_id),
                '$or': [
                    {'sender_id': ObjectId(session['user_id']), 'recipient_id': course['teacher_id']},
                    {'sender_id': course['teacher_id'], 'recipient_id': ObjectId(session['user_id'])}
                ]
            }).sort('sent_at', 1))
        else:
            # Teacher can see all messages in the course
            messages = list(db.messages.find({
                'course_id': ObjectId(course_id)
            }).sort('sent_at', 1))
        
        # Convert ObjectId to string for JSON serialization
        for message in messages:
            message['_id'] = str(message['_id'])
            message['sender_id'] = str(message['sender_id'])
            message['recipient_id'] = str(message['recipient_id']) if message.get('recipient_id') else None
            message['course_id'] = str(message['course_id'])
            message['sent_at'] = message['sent_at'].isoformat()
        
        return {'messages': messages}
        
    except Exception as e:
        return {'messages': []}

@app.route('/send_message/<course_id>', methods=['POST'])
def send_message(course_id):
    if 'user_id' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401
    
    try:
        content = sanitize_input(request.form.get('content', ''))
        recipient_id = request.form.get('recipient_id')
        
        if not content or len(content) < 1:
            return {'success': False, 'error': 'Message cannot be empty'}, 400
        
        if len(content) > 1000:
            return {'success': False, 'error': 'Message too long'}, 400
        
        message_data = {
            'course_id': ObjectId(course_id),
            'sender_id': ObjectId(session['user_id']),
            'content': content,
            'sent_at': datetime.now()
        }
        
        if recipient_id:
            message_data['recipient_id'] = ObjectId(recipient_id)
        elif session['role'] == 'student':
            course = db.courses.find_one({'_id': ObjectId(course_id)})
            if course:
                message_data['recipient_id'] = course['teacher_id']
            else:
                return {'success': False, 'error': 'Course not found'}, 404
        # For teachers, no specific recipient_id needed - they broadcast to course
        
        db.messages.insert_one(message_data)
        return {'success': True}
        
    except Exception as e:
        print(f'Message send error: {e}')
        return {'success': False, 'error': 'Failed to send message'}, 500

@app.route('/api/messages/<student_id>/<course_id>')
def api_get_messages(student_id, course_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return {'messages': []}, 403
    
    if db is None:
        return {'messages': []}
    
    try:
        messages = list(db.messages.find({
            'course_id': ObjectId(course_id),
            '$or': [
                {'sender_id': ObjectId(student_id), 'recipient_id': ObjectId(session['user_id'])},
                {'sender_id': ObjectId(session['user_id']), 'recipient_id': ObjectId(student_id)}
            ]
        }).sort('sent_at', 1))
        
        for message in messages:
            message['_id'] = str(message['_id'])
            message['sender_id'] = str(message['sender_id'])
            message['recipient_id'] = str(message['recipient_id']) if message.get('recipient_id') else None
            message['course_id'] = str(message['course_id'])
            message['sent_at'] = message['sent_at'].isoformat()
        
        return {'messages': messages}
        
    except Exception as e:
        return {'messages': []}

@app.route('/send_chat_message/<student_id>/<course_id>', methods=['POST'])
def send_chat_message(student_id, course_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return {'success': False}, 403
    
    try:
        content = sanitize_input(request.form.get('content', ''))
        
        if not content:
            return {'success': False}, 400
        
        db.messages.insert_one({
            'course_id': ObjectId(course_id),
            'sender_id': ObjectId(session['user_id']),
            'recipient_id': ObjectId(student_id),
            'content': content,
            'sent_at': datetime.now()
        })
        
        return {'success': True}
        
    except Exception as e:
        return {'success': False}, 500

@app.route('/send_student_message/<teacher_id>/<course_id>', methods=['POST'])
def send_student_message(teacher_id, course_id):
    if 'user_id' not in session or session['role'] != 'student':
        return {'success': False}, 403
    
    try:
        content = sanitize_input(request.form.get('content', ''))
        
        if not content:
            return {'success': False}, 400
        
        db.messages.insert_one({
            'course_id': ObjectId(course_id),
            'sender_id': ObjectId(session['user_id']),
            'recipient_id': ObjectId(teacher_id),
            'content': content,
            'sent_at': datetime.now()
        })
        
        return {'success': True}
        
    except Exception as e:
        return {'success': False}, 500

@app.route('/teacher_notification', methods=['GET', 'POST'])
def teacher_notification():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        message = request.form['message']
        target = request.form['target']
        
        if target == 'all_students':
            db.notifications.insert_one({
                'message': message,
                'target_role': 'student',
                'sender_id': ObjectId(session['user_id']),
                'sender_name': session['full_name'],
                'created_at': datetime.now()
            })
            flash('Notification sent to all students')
        else:
            course_id = target
            enrollments = db.enrollments.find({'course_id': ObjectId(course_id)})
            
            for enrollment in enrollments:
                db.notifications.insert_one({
                    'message': message,
                    'target_user_id': enrollment['student_id'],
                    'course_id': ObjectId(course_id),
                    'sender_id': ObjectId(session['user_id']),
                    'sender_name': session['full_name'],
                    'created_at': datetime.now()
                })
            
            course = db.courses.find_one({'_id': ObjectId(course_id)})
            flash(f'Notification sent to {course["name"]} students')
        
        return redirect(url_for('teacher_notification'))
    
    courses = list(db.courses.find({'teacher_id': ObjectId(session['user_id'])}))
    return render_template('teacher_notification.html', courses=courses)

@app.route('/student_messages')
def student_messages():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('dashboard'))
    
    if db is None:
        return render_template('student_messages.html', conversations=[])
    
    try:
        enrollments = db.enrollments.find({'student_id': ObjectId(session['user_id'])})
        course_ids = [e['course_id'] for e in enrollments]
        
        conversations = []
        for course_id in course_ids:
            course = db.courses.find_one({'_id': course_id})
            if not course:
                continue
                
            teacher = db.users.find_one({'_id': course['teacher_id']})
            if not teacher:
                continue
            
            latest_message = db.messages.find_one({
                'course_id': course_id,
                '$or': [
                    {'sender_id': ObjectId(session['user_id']), 'recipient_id': course['teacher_id']},
                    {'sender_id': course['teacher_id'], 'recipient_id': ObjectId(session['user_id'])}
                ]
            }, sort=[('sent_at', -1)])
            
            conversations.append({
                'course': course,
                'teacher': teacher,
                'latest_message': latest_message
            })
        
        return render_template('student_messages.html', conversations=conversations)
        
    except Exception as e:
        return render_template('student_messages.html', conversations=[])

@app.route('/student_chat_with_teacher/<teacher_id>/<course_id>')
def student_chat_with_teacher(teacher_id, course_id):
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('dashboard'))
    
    if db is None:
        flash('Database connection error')
        return redirect(url_for('student_messages'))
    
    try:
        course = db.courses.find_one({'_id': ObjectId(course_id)})
        teacher = db.users.find_one({'_id': ObjectId(teacher_id)})
        
        if not course or not teacher:
            flash('Course or teacher not found')
            return redirect(url_for('student_messages'))
        
        # Check if student is enrolled in the course
        enrollment = db.enrollments.find_one({
            'student_id': ObjectId(session['user_id']),
            'course_id': ObjectId(course_id)
        })
        
        if not enrollment:
            flash('You are not enrolled in this course')
            return redirect(url_for('student_messages'))
        
        # Get messages between student and teacher for this course
        messages = list(db.messages.find({
            'course_id': ObjectId(course_id),
            '$or': [
                {'sender_id': ObjectId(session['user_id']), 'recipient_id': ObjectId(teacher_id)},
                {'sender_id': ObjectId(teacher_id), 'recipient_id': ObjectId(session['user_id'])}
            ]
        }).sort('sent_at', 1))
        
        return render_template('student_chat.html', 
                             course=course, 
                             teacher=teacher, 
                             messages=messages)
        
    except Exception as e:
        flash('Error loading chat')
        return redirect(url_for('student_messages'))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        try:
            username = sanitize_input(request.form.get('username', ''))
            password = request.form.get('password', '')
            
            if not username or not password:
                flash('Username and password are required')
                return render_template('admin_login.html')
            
            if username == 'admin' and password == 'admin123':
                session['user_id'] = 'admin'
                session['username'] = 'admin'
                session['role'] = 'admin'
                session['full_name'] = 'Administrator'
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials')
                
        except Exception as e:
            flash('Login failed. Please try again.')
            print(f'Admin login error: {e}')
    
    return render_template('admin_login.html')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_code=404, error_message='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_code=500, error_message='Internal server error'), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('error.html', error_code=403, error_message='Access forbidden'), 403

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    try:
        if 'user_id' in session:
            join_room(f"user_{session['user_id']}")
            emit('status', {'msg': f"{session['full_name']} connected"})
    except Exception as e:
        print(f'WebSocket connect error: {e}')

@socketio.on('disconnect')
def handle_disconnect():
    try:
        if 'user_id' in session:
            leave_room(f"user_{session['user_id']}")
    except Exception as e:
        print(f'WebSocket disconnect error: {e}')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    try:
        init_db()
        port = int(os.environ.get('PORT', 5000))
        socketio.run(app, host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f'Application startup error: {e}')