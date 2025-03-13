from datetime import datetime, date
from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db=SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(64))
    qualification = db.Column(db.String(64))
    dob = db.Column(db.DateTime) 
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute!')
    
    @password.setter
    def password(self,password):
        self.password_hash=generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def parse_date(date_string):
        """Converts a string in 'YYYY-MM-DD' format to a Python date object."""
        try:
            return datetime.strptime(date_string, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Please use 'YYYY-MM-DD'.")

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    subject = db.relationship('Subject', backref=db.backref('chapters'))

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    title = db.Column(db.String(255))
    date_of_quiz = db.Column(db.Date)
    time_duration = db.Column(db.Time)
    remarks = db.Column(db.Text)
    chapter = db.relationship('Chapter', backref=db.backref('quizzes'))

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_statement = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(255))
    option2 = db.Column(db.String(255))
    option3 = db.Column(db.String(255))
    option4 = db.Column(db.String(255))
    correct_answer = db.Column(db.String(255))
    quiz = db.relationship('Quiz', backref=db.backref('questions'))

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_stamp_of_attempt = db.Column(db.DateTime)
    total_scored = db.Column(db.Integer)
    quiz = db.relationship('Quiz', backref=db.backref('scores'))
    user = db.relationship('User', backref=db.backref('scores'))

#creating the table if it doesn't exist
with app.app_context():
    db.drop_all()
    db.create_all()
    admin=User.query.filter_by(is_admin=True).first()
    if not admin:
        admin=User(username='admin',password='13121989',is_admin=True)
        db.session.add(admin)
        db.session.commit()

from sqlalchemy import inspect
    
'''# Creating the table if it doesn't exist
with app.app_context():
    # Check if the tables already exist
    if not inspect(db.engine).get_table_names():
        db.drop_all()
        db.create_all()  # Only create tables if they don't exist
    
    # Ensure admin user exists
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        admin = User(username='admin', password='13121989', is_admin=True)
        db.session.add(admin)
        db.session.commit() '''




        
