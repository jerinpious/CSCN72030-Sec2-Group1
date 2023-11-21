from flask import Flask, render_template, url_for, redirect , jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, login_user, LoginManager, current_user, login_required, logout_user
import json
import os
from flask import render_template, request
import subprocess
from FaceRecognition import run_face_recognition, stop_face_recognition
from audio import record_audio, stop_recording


app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisasecretkey'
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
AdminKey = '58JE3N14'

class User(UserMixin):
    def __init__(self, user_id, username, password):
        self.id = user_id
        self.username = username
        self.password = password

# Create a folder to store user data files
USER_DATA_FOLDER = os.path.join(app.root_path, 'user_data')
os.makedirs(USER_DATA_FOLDER, exist_ok=True)

def get_user_data_path(username):
    return os.path.join(USER_DATA_FOLDER, f'{username}.json')

@login_manager.user_loader
def load_user(user_id):
    user_data_path = get_user_data_path(user_id)
    if os.path.exists(user_data_path):
        with open(user_data_path, 'r') as file:
            user_data = json.load(file)
            return User(user_data['id'], user_data['username'], user_data['password'])
    return None

class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, field):
        user_data_path = get_user_data_path(field.data)
        if os.path.exists(user_data_path):
            raise ValidationError('That username already exists. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField(validators=[
                          InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                            InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')

class AdminLoginForm(FlaskForm):
    username = StringField(validators=[
                          InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    key = PasswordField(validators=[
                          InputRequired(), Length(min=8, max=8)], render_kw={"placeholder": "Admin Key"})

    password = PasswordField(validators=[
                            InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login As Administrator')


@app.route('/')

def home():
    return render_template('home.html')

import time
@app.route('/dashboard')
@login_required
def dashboard():
    data = []
    timestamp = int(time.time())
    with open('log.txt', 'r') as file:
        data.append(file.read())
    return render_template('dashboard.html', username=current_user.username, timestamp=timestamp, data=data)

@app.route('/admin_dashboard')
@login_required
def admindashboard():
    timestamp = int(time.time())
    return render_template('admindash.html', username=current_user.username, timestamp=timestamp)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user_id = form.username.data
        user_data = {'id': user_id, 'username': form.username.data, 'password': hashed_password}
        user_data_path = get_user_data_path(user_id)

        with open(user_data_path, 'w') as file:
            json.dump(user_data, file)

        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user_data_path = get_user_data_path(form.username.data)
        if os.path.exists(user_data_path):
            with open(user_data_path, 'r') as file:
                user_data = json.load(file)

            if bcrypt.check_password_hash(user_data['password'], form.password.data):
                user = User(user_data['id'], user_data['username'], user_data['password'])
                login_user(user)
                return redirect(url_for('dashboard'))

    return render_template('login.html', form=form)

# Admin login route
@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    form = AdminLoginForm()

    if form.validate_on_submit():
        user_data_path = get_user_data_path(form.username.data)
        if os.path.exists(user_data_path):
            with open(user_data_path, 'r') as file:
                user_data = json.load(file)

            # Check if the entered key matches the AdminKey
            if (form.key.data==AdminKey):
                # Check if the entered password is correct
                if bcrypt.check_password_hash(user_data['password'], form.password.data):
                    user = User(user_data['id'], user_data['username'], user_data['password'])
                    login_user(user)
                    return redirect(url_for('admindashboard'))

    return render_template('admin.html', form=form)

@app.route('/alerts')
@login_required
def alerts():
    return render_template('Alerts.html', username=current_user.username)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# for the face recognition
@app.route('/start_face_recognition', methods=['POST'])
def start_face_recognition():
    # Trigger the face recognition script
    run_face_recognition()
    return jsonify({'message': 'Face recognition started'})

@app.route('/stop_face_recognition', methods=['POST'])
def stop_face_recognition_route():
    # Trigger the stop face recognition function
    stop_face_recognition()
    return jsonify({'message': 'Face recognition stopped'})


# For the audio recording
@app.route('/start_audio_recording', methods=['POST'])
def start_audio_recording():
    # Trigger the audio recording script
    record_audio()
    return jsonify({'message': 'Audio recording started'})

# For stopping audio recording
@app.route('/stop_audio_recording', methods=['POST'])
def stop_audio_recording():
    # Trigger the stop recording function
    stop_recording()
    return jsonify({'message': 'Audio recording stopped'})


if __name__ == '__main__':
    app.run(debug=True)