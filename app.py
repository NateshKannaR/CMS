from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from datetime import datetime, timedelta
import uuid
import urllib.parse

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.permanent_session_lifetime = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# MongoDB connection (Atlas)
try:
    print('Connecting to MongoDB Atlas...')
    
    # Connect to MongoDB Atlas
    client = MongoClient('mongodb+srv://Natesh:Natesh1974@cluster0.wwp3oig.mongodb.net/')
    db = client.cms_database
    
    # Test connection
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
        # MongoDB collections are created automatically when first document is inserted
        # Create indexes for better performance
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if db is None:
            flash('Database connection error. Please try again later.')
            return render_template('register.html')
            
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        full_name = request.form['full_name']
        
        hashed_password = generate_password_hash(password)
        
        try:
            # Check if user already exists
            if db.users.find_one({'$or': [{'username': username}, {'email': email}]}):
                flash('Username or email already exists')
            else:
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
            flash(f'Database error: {str(e)}')
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if db is None:
        flash('Database connection error')
        return render_template('dashboard.html', courses=[], user_email='', user_joined_date='')
    
    try:
        # Get user details
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

@app.route('/course/<course_id>')
def course_detail(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get course details
    course = db.courses.find_one({'_id': ObjectId(course_id)})
    
    # Get assignments
    assignments = list(db.assignments.find({'course_id': ObjectId(course_id)}).sort('due_date', 1))
    
    # Get materials
    materials = list(db.materials.find({'course_id': ObjectId(course_id)}).sort('uploaded_at', -1))
    
    # Get private messages for current user
    if session['role'] == 'teacher':
        # Teachers see all student messages to them
        messages = list(db.messages.aggregate([
            {'$match': {'course_id': ObjectId(course_id)}},
            {'$lookup': {
                'from': 'users',
                'localField': 'sender_id',
                'foreignField': '_id',
                'as': 'sender'
            }},
            {'$sort': {'sent_at': -1}}
        ]))
    else:
        # Students see only their own conversation with teacher
        messages = list(db.messages.aggregate([
            {'$match': {
                'course_id': ObjectId(course_id),
                '$or': [
                    {'sender_id': ObjectId(session['user_id'])},
                    {'recipient_id': ObjectId(session['user_id'])}
                ]
            }},
            {'$lookup': {
                'from': 'users',
                'localField': 'sender_id',
                'foreignField': '_id',
                'as': 'sender'
            }},
            {'$sort': {'sent_at': -1}}
        ]))
    
    return render_template('course_detail.html', course=course, assignments=assignments, materials=materials, messages=messages)

@app.route('/create_course', methods=['GET', 'POST'])
def create_course():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        course_code = request.form['course_code']
        
        # Check if course code already exists
        if db.courses.find_one({'course_code': course_code}):
            flash('Course code already exists')
        else:
            db.courses.insert_one({
                'name': name,
                'description': description,
                'teacher_id': ObjectId(session['user_id']),
                'course_code': course_code,
                'created_at': datetime.now()
            })
            flash('Course created successfully')
            return redirect(url_for('dashboard'))
    
    return render_template('create_course.html')

@app.route('/join_course', methods=['POST'])
def join_course():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('dashboard'))
    
    course_code = request.form['course_code']
    
    # Find course by code
    course = db.courses.find_one({'course_code': course_code})
    
    if course:
        # Check if already enrolled
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
    
    # Get assignment details
    assignment = db.assignments.find_one({'_id': ObjectId(assignment_id)})
    
    # Get user's submission if exists
    submission = db.submissions.find_one({
        'assignment_id': ObjectId(assignment_id),
        'student_id': ObjectId(session['user_id'])
    })
    
    # If teacher, get all submissions
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
    
    # Check if submission already exists
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

@app.route('/send_message/<course_id>', methods=['POST'])
def send_message(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    content = request.form['content']
    recipient_id = request.form.get('recipient_id')
    
    message_data = {
        'course_id': ObjectId(course_id),
        'sender_id': ObjectId(session['user_id']),
        'content': content,
        'sent_at': datetime.now()
    }
    
    if recipient_id:
        message_data['recipient_id'] = ObjectId(recipient_id)
    elif session['role'] == 'student':
        # Student sending to teacher - find course teacher
        course = db.courses.find_one({'_id': ObjectId(course_id)})
        message_data['recipient_id'] = course['teacher_id']
    
    db.messages.insert_one(message_data)
    
    return redirect(url_for('course_detail', course_id=course_id))

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['username'] != 'admin':
        flash('Admin access required')
        return redirect(url_for('login'))
    
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

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    full_name = request.form['full_name']
    email = request.form['email']
    
    update_data = {'full_name': full_name, 'email': email}
    
    # Handle profile photo upload
    if 'profile_photo' in request.files:
        file = request.files['profile_photo']
        if file.filename != '':
            filename = secure_filename(file.filename)
            photo_filename = f"{uuid.uuid4()}_{filename}"
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
        {'$set': {'password': hashed_new_password, 'plain_password': new_password}}
    )
    
    flash('Password changed successfully')
    return redirect(url_for('dashboard'))

@app.route('/notifications')
def get_notifications():
    if 'user_id' not in session:
        return {'notifications': []}
    
    # Get notifications for current user
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

@app.route('/create_notification', methods=['GET', 'POST'])
def create_notification():
    if 'user_id' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        message = request.form['message']
        target_role = request.form['target_role']
        
        db.notifications.insert_one({
            'message': message,
            'target_role': target_role,
            'created_at': datetime.now()
        })
        
        flash('Notification sent successfully')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('create_notification.html')

@app.route('/view_notifications')
def view_notifications():
    if 'user_id' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))
    
    notifications = list(db.notifications.find().sort('created_at', -1))
    return render_template('view_notifications.html', notifications=notifications)

@app.route('/delete_notification/<notification_id>')
def delete_notification(notification_id):
    if 'user_id' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))
    
    db.notifications.delete_one({'_id': ObjectId(notification_id)})
    flash('Notification deleted successfully')
    return redirect(url_for('view_notifications'))

@app.route('/chatbot', methods=['POST'])
def chatbot():
    if 'user_id' not in session or session['role'] != 'student':
        return {'response': 'Access denied'}, 403
    
    data = request.get_json()
    message = data.get('message', '').lower()
    
    # Check custom training data first
    training_match = db.ai_training.find_one({'question': {'$regex': message, '$options': 'i'}})
    if training_match:
        return {'response': training_match['answer']}
    
    # Check for partial matches
    for word in message.split():
        if len(word) > 3:
            training_match = db.ai_training.find_one({'question': {'$regex': word, '$options': 'i'}})
            if training_match:
                return {'response': training_match['answer']}
    
    # Default responses
    if 'hello' in message or 'hi' in message:
        response = "Hello! I'm here to help you with your studies. What would you like to know?"
    elif 'assignment' in message:
        response = "For assignments, check your course dashboard. You can submit work, view due dates, and see grades there."
    elif 'course' in message:
        response = "To join a course, get the course code from your teacher and use the 'Join Course' option on your dashboard."
    elif 'grade' in message:
        response = "You can view your grades in the assignment details. Teachers will provide feedback along with grades."
    else:
        response = "I'm here to help! Try asking about courses, assignments, grades, or submissions. You can also ask questions that the admin has trained me on."
    
    return {'response': response}

@app.route('/upload_material/<course_id>', methods=['POST'])
def upload_material(course_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    title = request.form['title']
    description = request.form['description']
    file_path = None
    
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
            file.save(file_path)
    
    db.materials.insert_one({
        'title': title,
        'description': description,
        'course_id': ObjectId(course_id),
        'file_path': file_path,
        'filename': file.filename if 'file' in request.files else None,
        'uploaded_by': ObjectId(session['user_id']),
        'uploaded_at': datetime.now()
    })
    
    flash('Material uploaded successfully')
    return redirect(url_for('course_detail', course_id=course_id))

@app.route('/download_material/<material_id>')
def download_material(material_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    material = db.materials.find_one({'_id': ObjectId(material_id)})
    if material and material['file_path']:
        from flask import send_file
        return send_file(material['file_path'], as_attachment=True, download_name=material['filename'])
    
    flash('File not found')
    return redirect(request.referrer)

@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        max_participants = int(request.form['max_participants'])
        question_time = int(request.form['question_time'])
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
        
        quiz_result = db.quizzes.insert_one({
            'title': title,
            'quiz_code': quiz_code,
            'teacher_id': ObjectId(session['user_id']),
            'questions': questions,
            'max_participants': max_participants,
            'question_time': question_time,
            'status': 'waiting',
            'current_question': 0,
            'participants': [],
            'created_at': datetime.now()
        })
        
        return redirect(url_for('manage_quiz', quiz_id=quiz_result.inserted_id))
    
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
        
        # Add participant
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

@app.route('/manage_quiz/<quiz_id>')
def manage_quiz(quiz_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id)})
    return render_template('manage_quiz.html', quiz=quiz)

@app.route('/start_quiz/<quiz_id>', methods=['POST'])
def start_quiz(quiz_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return {'success': False}, 403
    
    db.quizzes.update_one(
        {'_id': ObjectId(quiz_id)},
        {'$set': {'status': 'active', 'current_question': 0}}
    )
    
    return {'success': True}

@app.route('/pause_quiz/<quiz_id>', methods=['POST'])
def pause_quiz(quiz_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return {'success': False}, 403
    
    db.quizzes.update_one(
        {'_id': ObjectId(quiz_id)},
        {'$set': {'status': 'paused'}}
    )
    
    return {'success': True}

@app.route('/stop_quiz/<quiz_id>', methods=['POST'])
def stop_quiz(quiz_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return {'success': False}, 403
    
    db.quizzes.update_one(
        {'_id': ObjectId(quiz_id)},
        {'$set': {'status': 'stopped'}}
    )
    
    return {'success': True}

@app.route('/next_question/<quiz_id>', methods=['POST'])
def next_question(quiz_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return {'success': False}, 403
    
    quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id)})
    next_q = quiz['current_question'] + 1
    
    db.quizzes.update_one(
        {'_id': ObjectId(quiz_id)},
        {'$set': {'current_question': next_q}}
    )
    
    return {'success': True, 'question_number': next_q}

@app.route('/quiz_stats/<quiz_id>')
def quiz_stats(quiz_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return {'success': False}, 403
    
    quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id)})
    current_q = quiz.get('current_question', 0)
    
    # Count answers for current question
    answer_counts = [0, 0, 0, 0]
    total_answered = 0
    
    for participant in quiz.get('participants', []):
        answers = participant.get('answers', [])
        for ans in answers:
            if ans['question'] == current_q:
                answer_counts[ans['answer']] += 1
                total_answered += 1
                break
    
    return {
        'answer_counts': answer_counts,
        'total_participants': len(quiz.get('participants', [])),
        'total_answered': total_answered,
        'question_number': current_q + 1
    }

@app.route('/submit_answer/<quiz_id>', methods=['POST'])
def submit_answer(quiz_id):
    if 'user_id' not in session or session['role'] != 'student':
        return {'success': False}, 403
    
    data = request.get_json()
    answer = data.get('answer')
    question_index = data.get('question_index')
    
    quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id)})
    correct_answer = quiz['questions'][question_index]['correct_answer']
    
    # Calculate points (faster answers get more points)
    points = 100 if answer == correct_answer else 0
    
    # Update participant score
    db.quizzes.update_one(
        {'_id': ObjectId(quiz_id), 'participants.user_id': ObjectId(session['user_id'])},
        {
            '$inc': {'participants.$.score': points},
            '$push': {'participants.$.answers': {'question': question_index, 'answer': answer, 'points': points}}
        }
    )
    
    return {'success': True, 'correct': answer == correct_answer, 'points': points}

@app.route('/teacher_notification', methods=['GET', 'POST'])
def teacher_notification():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        message = request.form['message']
        target = request.form['target']
        
        if target == 'all_students':
            # Send to all students
            db.notifications.insert_one({
                'message': message,
                'target_role': 'student',
                'sender_id': ObjectId(session['user_id']),
                'sender_name': session['full_name'],
                'created_at': datetime.now()
            })
            flash('Notification sent to all students')
        else:
            # Send to specific course students
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
    
    # Get teacher's courses
    courses = list(db.courses.find({'teacher_id': ObjectId(session['user_id'])}))
    return render_template('teacher_notification.html', courses=courses)

@app.route('/calendar')
def calendar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get assignments with due dates
    if session['role'] == 'teacher':
        courses = list(db.courses.find({'teacher_id': ObjectId(session['user_id'])}))
        course_ids = [c['_id'] for c in courses]
        assignments = list(db.assignments.find({'course_id': {'$in': course_ids}}))
    else:
        enrollments = db.enrollments.find({'student_id': ObjectId(session['user_id'])})
        course_ids = [e['course_id'] for e in enrollments]
        assignments = list(db.assignments.find({'course_id': {'$in': course_ids}}))
    
    # Get course names
    courses_dict = {c['_id']: c['name'] for c in db.courses.find({'_id': {'$in': course_ids}})}
    
    return render_template('calendar.html', assignments=assignments, courses=courses_dict)

@app.route('/video_lectures/<course_id>')
def video_lectures(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    course = db.courses.find_one({'_id': ObjectId(course_id)})
    lectures = list(db.video_lectures.find({'course_id': ObjectId(course_id)}).sort('uploaded_at', -1))
    
    return render_template('video_lectures.html', course=course, lectures=lectures)

@app.route('/upload_video/<course_id>', methods=['POST'])
def upload_video(course_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    title = request.form['title']
    description = request.form['description']
    video_url = request.form['video_url']
    
    db.video_lectures.insert_one({
        'title': title,
        'description': description,
        'video_url': video_url,
        'course_id': ObjectId(course_id),
        'uploaded_by': ObjectId(session['user_id']),
        'uploaded_at': datetime.now()
    })
    
    flash('Video lecture uploaded successfully')
    return redirect(url_for('video_lectures', course_id=course_id))

@app.route('/whiteboard/<course_id>')
def whiteboard(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    course = db.courses.find_one({'_id': ObjectId(course_id)})
    return render_template('whiteboard.html', course=course)

@app.route('/attendance/<course_id>')
def attendance(course_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    course = db.courses.find_one({'_id': ObjectId(course_id)})
    
    # Get enrolled students
    enrollments = list(db.enrollments.aggregate([
        {'$match': {'course_id': ObjectId(course_id)}},
        {'$lookup': {
            'from': 'users',
            'localField': 'student_id',
            'foreignField': '_id',
            'as': 'student'
        }}
    ]))
    
    # Get today's attendance
    today = datetime.now().strftime('%Y-%m-%d')
    attendance_records = list(db.attendance.find({
        'course_id': ObjectId(course_id),
        'date': today
    }))
    
    # Create attendance status dict
    attendance_status = {}
    for record in attendance_records:
        attendance_status[str(record['student_id'])] = record['status']
    
    return render_template('attendance.html', course=course, enrollments=enrollments, 
                         attendance_status=attendance_status, today=today)

@app.route('/mark_attendance/<course_id>', methods=['POST'])
def mark_attendance(course_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    student_id = request.form['student_id']
    status = request.form['status']
    date = request.form['date']
    
    # Update or insert attendance record
    db.attendance.update_one(
        {
            'course_id': ObjectId(course_id),
            'student_id': ObjectId(student_id),
            'date': date
        },
        {
            '$set': {
                'status': status,
                'marked_by': ObjectId(session['user_id']),
                'marked_at': datetime.now()
            }
        },
        upsert=True
    )
    
    return redirect(url_for('attendance', course_id=course_id))

@app.route('/attendance_report/<course_id>')
def attendance_report(course_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    course = db.courses.find_one({'_id': ObjectId(course_id)})
    
    # Get all attendance records for this course
    records = list(db.attendance.aggregate([
        {'$match': {'course_id': ObjectId(course_id)}},
        {'$lookup': {
            'from': 'users',
            'localField': 'student_id',
            'foreignField': '_id',
            'as': 'student'
        }},
        {'$sort': {'date': -1}}
    ]))
    
    return render_template('attendance_report.html', course=course, records=records)

@app.route('/teacher_messages')
def teacher_messages():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    # Get all students who have messaged this teacher
    teacher_courses = list(db.courses.find({'teacher_id': ObjectId(session['user_id'])}))
    course_ids = [c['_id'] for c in teacher_courses]
    
    # Get unique students with their latest message
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

@app.route('/chat/<student_id>/<course_id>')
def chat_with_student(student_id, course_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    student = db.users.find_one({'_id': ObjectId(student_id)})
    course = db.courses.find_one({'_id': ObjectId(course_id)})
    
    # Get all messages between teacher and this student in this course
    messages = list(db.messages.find({
        'course_id': ObjectId(course_id),
        '$or': [
            {'sender_id': ObjectId(session['user_id']), 'recipient_id': ObjectId(student_id)},
            {'sender_id': ObjectId(student_id), 'recipient_id': ObjectId(session['user_id'])}
        ]
    }).sort('sent_at', 1))
    
    return render_template('chat_window.html', student=student, course=course, messages=messages)

@app.route('/send_chat_message/<student_id>/<course_id>', methods=['POST'])
def send_chat_message(student_id, course_id):
    if 'user_id' not in session:
        return {'success': False}, 403
    
    content = request.form['content']
    
    db.messages.insert_one({
        'course_id': ObjectId(course_id),
        'sender_id': ObjectId(session['user_id']),
        'recipient_id': ObjectId(student_id),
        'content': content,
        'sent_at': datetime.now()
    })
    
    return redirect(url_for('chat_with_student', student_id=student_id, course_id=course_id))

@app.route('/admin_practice_quiz', methods=['GET', 'POST'])
def admin_practice_quiz():
    if 'user_id' not in session or session['username'] != 'admin':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        difficulty = request.form['difficulty']
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
        
        db.practice_quizzes.insert_one({
            'title': title,
            'category': category,
            'difficulty': difficulty,
            'questions': questions,
            'created_by': ObjectId(session['user_id']),
            'created_at': datetime.now()
        })
        
        flash('Practice quiz created successfully')
        return redirect(url_for('admin_practice_quiz'))
    
    # Get existing practice quizzes
    quizzes = list(db.practice_quizzes.find().sort('created_at', -1))
    return render_template('admin_practice_quiz.html', quizzes=quizzes)

@app.route('/practice_quiz')
def practice_quiz():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('dashboard'))
    
    # Get all practice quizzes
    quizzes = list(db.practice_quizzes.find())
    return render_template('practice_quiz_list.html', quizzes=quizzes)

@app.route('/take_practice_quiz/<quiz_id>')
def take_practice_quiz(quiz_id):
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('dashboard'))
    
    quiz = db.practice_quizzes.find_one({'_id': ObjectId(quiz_id)})
    return render_template('take_practice_quiz.html', quiz=quiz)

@app.route('/submit_practice_quiz/<quiz_id>', methods=['POST'])
def submit_practice_quiz(quiz_id):
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('dashboard'))
    
    quiz = db.practice_quizzes.find_one({'_id': ObjectId(quiz_id)})
    score = 0
    total = len(quiz['questions'])
    results = []
    
    for i, question in enumerate(quiz['questions']):
        user_answer = int(request.form.get(f'answer_{i}', -1))
        correct_answer = question['correct_answer']
        is_correct = user_answer == correct_answer
        
        if is_correct:
            score += 1
            
        results.append({
            'question': question['question'],
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct,
            'options': question['options']
        })
    
    # Save practice result
    db.practice_results.insert_one({
        'student_id': ObjectId(session['user_id']),
        'quiz_id': ObjectId(quiz_id),
        'score': score,
        'total': total,
        'percentage': round((score/total)*100, 2),
        'completed_at': datetime.now()
    })
    
    return render_template('practice_quiz_result.html', 
                         quiz=quiz, score=score, total=total, 
                         percentage=round((score/total)*100, 2), results=results)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, threaded=True)