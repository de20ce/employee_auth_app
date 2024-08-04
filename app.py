from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
import os
import cv2
import numpy as np
import face_recognition
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
Bootstrap(app)
db = SQLAlchemy(app)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    face_encoding = db.Column(db.PickleType, nullable=False)

# Ensure tables are created
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if 'file' not in request.files or request.files['file'].filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        name = request.form['name']
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        image = face_recognition.load_image_file(filepath)
        face_encodings = face_recognition.face_encodings(image)
        
        if len(face_encodings) == 0:
            flash('No face detected in the image', 'danger')
            return redirect(request.url)
        
        new_employee = Employee(name=name, face_encoding=face_encodings[0])
        db.session.add(new_employee)
        db.session.commit()
        
        flash('Registration successful', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/authenticate', methods=['GET', 'POST'])
def authenticate():
    if request.method == 'POST':
        image_data = request.form['imageData']
        
        # Decode the image from base64
        image_data = base64.b64decode(image_data.split(',')[1])
        image = Image.open(BytesIO(image_data))
        image = np.array(image)
        
        face_encodings = face_recognition.face_encodings(image)
        
        if len(face_encodings) == 0:
            flash('No face detected in the image', 'danger')
            return redirect(request.url)
        
        employees = Employee.query.all()
        known_face_encodings = [employee.face_encoding for employee in employees]
        known_face_names = [employee.name for employee in employees]
        
        matches = face_recognition.compare_faces(known_face_encodings, face_encodings[0])
        name = "Unknown"
        
        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]
        
        flash(f'Authenticated as: {name}', 'success' if name != "Unknown" else 'danger')
        return redirect(url_for('index'))
    
    return render_template('authenticate.html')

if __name__ == '__main__':
    app.run(debug=True)
