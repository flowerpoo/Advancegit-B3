from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import re
from bson import ObjectId

import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

mongo_uri = os.getenv("MONGO_URI")

# Flask-Login config
app.config['SECRET_KEY'] = 'mysecret'
login_manager = LoginManager()
login_manager.init_app(app)

client = MongoClient(mongo_uri)
db = client['UserDB']
users_collection = db['users']
tasks_collection = db['tasks']

class User(UserMixin):
    def __init__(self, user_id, is_admin=False):
        self.id = user_id
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    u = users_collection.find_one({"user_id": user_id})
    if not u:
        return None
    return User(str(u['_id']) , u.get('is_admin', False))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        user_id = request.form['user_id']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not re.match("^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password):
            return "Password doesn't meet criteria"

        if password == confirm_password:
            user_data = {'name': name, 'email': email, 'user_id': user_id, 'password': password, 'is_admin': False}
            users_collection.insert_one(user_data)
            return redirect(url_for('login'))
        else:
            return "Passwords do not match"

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({"user_id": user_id, "password": password})
        
        if user:
            user_obj = User(user['user_id'])
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials", 401

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return 'Logged out successfully!'


@app.route('/tasks', methods=['POST'])
@login_required
def create_task():

    if not current_user.is_admin:
        return "Unauthorized", 401
    
    title = request.form['title']
    description = request.form['description']
    assigned_user_id = request.form['assigned_user_id']

    task = {'title': title, 'description': description, 'assigned_user_id': assigned_user_id, 'creator_user_id': current_user.id}
    tasks_collection.insert_one(task)

    return redirect(url_for('dashboard'))

@app.route('/tasks', methods=['GET'])
@login_required
def get_tasks():

    if current_user.is_admin:
        tasks = list(tasks_collection.find({}))
    else:
        tasks = list(tasks_collection.find({'assigned_user_id': current_user.id}))

    return jsonify(tasks)

@app.route('/tasks/<task_id>', methods=['PUT'])
@login_required
def update_task(task_id):

    if not current_user.is_admin:
        return "Unauthorized", 401

    updated_data = request.form.to_dict()
    tasks_collection.update_one({'_id': ObjectId(task_id)}, {'$set': updated_data})
    return redirect(url_for('dashboard'))

@app.route('/tasks/<task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    if not current_user.is_admin:
        return "Unauthorized", 401

    tasks_collection.delete_one({'_id': ObjectId(task_id)})
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    all_users = []
    tasks = []

    current_user_name = users_collection.find_one({"_id": ObjectId(str(current_user.id))})["user_id"]
    if current_user.is_admin:
        all_users = list(users_collection.find({}, {'user_id': 1}))
        tasks = list(tasks_collection.find({}))
    else:
        tasks = list(tasks_collection.find({'assigned_user_id': current_user_name}))

    return render_template('dashboard.html', current_user=current_user, all_users=all_users, tasks=tasks)



if __name__ == '__main__':
    app.run(debug=True)
