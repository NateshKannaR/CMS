from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'admin-secret-key'
app.permanent_session_lifetime = timedelta(hours=24)

# MongoDB connection
client = MongoClient('mongodb+srv://Natesh:Natesh1974@cluster0.wwp3oig.mongodb.net/')
db = client.cms_database

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'admin_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = db.users.find_one({'username': username, 'role': 'admin'})
        
        if admin and check_password_hash(admin['password'], password):
            session.permanent = True
            session['admin_id'] = str(admin['_id'])
            session['admin_name'] = admin['full_name']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid admin credentials')
    
    return render_template('admin_login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = db.users.find_one({'username': username, 'role': 'admin'})
        
        if admin and check_password_hash(admin['password'], password):
            session['admin_id'] = str(admin['_id'])
            session['admin_name'] = admin['full_name']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid admin credentials')
    
    return render_template('admin_login.html')

@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    pending_teachers = list(db.users.find({'role': 'teacher', 'status': 'pending'}))
    all_teachers = list(db.users.find({'role': 'teacher', 'status': {'$ne': 'pending'}}))
    all_students = list(db.users.find({'role': 'student'}))
    
    return render_template('admin_dashboard_separate.html', 
                         pending_teachers=pending_teachers,
                         all_teachers=all_teachers,
                         all_students=all_students)

@app.route('/approve/<user_id>')
def approve_teacher(user_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'status': 'approved'}})
    flash('Teacher approved successfully')
    return redirect(url_for('dashboard'))

@app.route('/reject/<user_id>')
def reject_teacher(user_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'status': 'rejected'}})
    flash('Teacher rejected')
    return redirect(url_for('dashboard'))

@app.route('/bulk_upload', methods=['GET', 'POST'])
def bulk_upload():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('No file selected')
            return redirect(url_for('bulk_upload'))
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('No file selected')
            return redirect(url_for('bulk_upload'))
        
        if file and file.filename.endswith('.csv'):
            import csv
            from io import StringIO
            from werkzeug.security import generate_password_hash
            
            stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.DictReader(stream)
            
            success_count = 0
            error_count = 0
            
            for row in csv_input:
                try:
                    # Check if user already exists
                    if not db.users.find_one({'$or': [{'username': row['username']}, {'email': row['email']}]}):
                        user_data = {
                            'username': row['username'],
                            'email': row['email'],
                            'password': generate_password_hash(row['password']),
                            'plain_password': row['password'],
                            'role': row['role'],
                            'full_name': row['full_name'],
                            'status': 'approved' if row['role'] == 'student' else 'pending',
                            'created_at': datetime.now()
                        }
                        db.users.insert_one(user_data)
                        success_count += 1
                    else:
                        error_count += 1
                except:
                    error_count += 1
            
            flash(f'Upload complete: {success_count} users added, {error_count} errors')
        else:
            flash('Please upload a CSV file')
    
    return render_template('bulk_upload.html')



@app.route('/add_user', methods=['POST'])
def add_user():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    from werkzeug.security import generate_password_hash
    
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']
    full_name = request.form['full_name']
    
    if db.users.find_one({'$or': [{'username': username}, {'email': email}]}):
        flash('Username or email already exists')
    else:
        db.users.insert_one({
            'username': username,
            'email': email,
            'password': generate_password_hash(password),
            'plain_password': password,
            'role': role,
            'full_name': full_name,
            'status': 'approved',
            'created_at': datetime.now()
        })
        flash(f'{role.title()} added successfully')
    
    return redirect(url_for('dashboard'))

@app.route('/delete_user/<user_id>')
def delete_user(user_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    db.users.delete_one({'_id': ObjectId(user_id)})
    flash('User deleted successfully')
    return redirect(url_for('dashboard'))

@app.route('/create_notification', methods=['GET', 'POST'])
def create_notification():
    if 'admin_id' not in session:
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
        return redirect(url_for('dashboard'))
    
    return render_template('create_notification.html')

@app.route('/view_notifications')
def view_notifications():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    notifications = list(db.notifications.find().sort('created_at', -1))
    return render_template('view_notifications.html', notifications=notifications)

@app.route('/delete_notification/<notification_id>')
def delete_notification(notification_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    db.notifications.delete_one({'_id': ObjectId(notification_id)})
    flash('Notification deleted successfully')
    return redirect(url_for('view_notifications'))

@app.route('/train_ai', methods=['GET', 'POST'])
def train_ai():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'csv_file' in request.files:
            file = request.files['csv_file']
            if file and file.filename.endswith('.csv'):
                import csv
                from io import StringIO
                
                stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_input = csv.DictReader(stream)
                
                for row in csv_input:
                    if 'question' in row and 'answer' in row:
                        db.ai_training.insert_one({
                            'question': row['question'].lower(),
                            'answer': row['answer'],
                            'created_at': datetime.now()
                        })
                
                flash('CSV training data uploaded successfully')
        else:
            question = request.form['question']
            answer = request.form['answer']
            
            db.ai_training.insert_one({
                'question': question.lower(),
                'answer': answer,
                'created_at': datetime.now()
            })
            
            flash('Training data added successfully')
        
        return redirect(url_for('train_ai'))
    
    training_data = list(db.ai_training.find().sort('created_at', -1))
    return render_template('train_ai.html', training_data=training_data)

@app.route('/delete_training/<training_id>')
def delete_training(training_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    db.ai_training.delete_one({'_id': ObjectId(training_id)})
    flash('Training data deleted successfully')
    return redirect(url_for('train_ai'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)