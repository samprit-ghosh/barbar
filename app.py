from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
from collections import Counter
from flask import jsonify


# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///appointments.db'  # SQLite database
app.config['SECRET_KEY'] = 'your_secret_key'  # Secret key for session management
# app.config['MAIL_SERVER'] = 'smtp.example.com'  # SMTP server for sending emails
# app.config['MAIL_PORT'] = 587  # SMTP port
# app.config['MAIL_USE_TLS'] = True  # Use TLS for secure email
# app.config['MAIL_USERNAME'] = 'your_email@example.com'  # Your email address
# app.config['MAIL_PASSWORD'] = 'your_email_password'  # Your email password

# Initialize extensions
db = SQLAlchemy(app)
# mail = Mail(app)

# Define the Appointment model
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    time = db.Column(db.String(80), nullable=False)

    # with app.app_context():
    #  db.create_all()

    def __repr__(self):
        return f'<Appointment {self.name}>'

# Define the User model for admin login
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Create the database tables
with app.app_context():

    db.create_all()  # Create tables with the new schema



    # Create a default admin user if it doesn't exist
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin')
        admin_user.set_password('admin123')  # Set a default password
        db.session.add(admin_user)
        db.session.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/book', methods=['GET', 'POST'])
def book():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        category = request.form['category']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')  # Convert string to datetime
        time = request.form['time']

        # Create a new appointment
        new_appointment = Appointment(name=name, email=email, date=date, time=time,phone=phone,category=category)
        db.session.add(new_appointment)
        db.session.commit()

        # Send email to admin
        msg = Message('New Appointment Booking', sender='your_email@example.com', recipients=['admin@example.com'])
        msg.body = f'You have a new appointment booking from {name} ({email}) on {date} at {time}.'
        # mail.send(msg)

        flash('Appointment booked successfully!')
        return redirect(url_for('book'))

    return render_template('book.html')

# Admin login route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['admin_logged_in'] = True
            flash('Logged in successfully!')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password')

    return render_template('admin_login.html')

# Admin logout route
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)  # Clear the session
    flash('Logged out successfully!')
    return redirect(url_for('index'))

# Protected admin route
@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        flash('Please log in to access the admin panel.')
        return redirect(url_for('admin_login'))

    appointments = Appointment.query.all()

    # Prepare data for category-wise pie chart
    categories = [appointment.category for appointment in appointments]
    category_counts = Counter(categories)
    category_data = {
        'labels': list(category_counts.keys()),
        'data': list(category_counts.values())
    }

    # Prepare data for month-wise bar chart
    months = [appointment.date.strftime('%B') for appointment in appointments]
    month_counts = Counter(months)
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December']
    monthly_data = {
        'labels': month_order,
        'data': [month_counts.get(month, 0) for month in month_order]
    }

    return render_template('admin.html', appointments=appointments, 
                           category_data=category_data, monthly_data=monthly_data)

# Run the application
if __name__ == '__main__':
   
    app.run(debug=True)