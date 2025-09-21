from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

# MongoDB connection
mongo_uri = os.environ.get('MONGODB_URI', 'mongodb+srv://Natesh:Natesh1974@cluster0.wwp3oig.mongodb.net/')
client = MongoClient(mongo_uri)
db = client.cms_database

# Create admin user
admin_user = {
    'username': 'admin',
    'email': 'admin@brainlow.com',
    'password': generate_password_hash('admin123'),
    'plain_password': 'admin123',
    'role': 'admin',
    'full_name': 'BrainLow Admin',
    'status': 'approved',
    'created_at': datetime.now()
}

# Insert admin if doesn't exist
if not db.users.find_one({'username': 'admin'}):
    db.users.insert_one(admin_user)
    print("Admin user created successfully!")
    print("Username: admin")
    print("Password: admin123")
else:
    print("Admin user already exists!")

client.close()