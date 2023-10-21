from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import re

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

class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

@login_manager.user_loader
def load_user(user_id):
    u = users_collection.find_one({"user_id": user_id})
    if not u:
        return None
    return User(u['user_id'])

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
            user_data = {'name': name, 'email': email, 'user_id': user_id, 'password': password}
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
            return "Logged in successfully"
        else:
            return "Invalid credentials"

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return 'Logged out successfully!'

if __name__ == '__main__':
    app.run(debug=True)
