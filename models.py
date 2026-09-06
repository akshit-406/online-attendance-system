from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(100),unique=True,nullable=False)
    email = db.Column(db.String(100),unique=True,nullable=False)
    password_hash = db.Column(db.String(250),nullable=False)
    role = db.Column(db.String(20),nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash,password)


class Class(db.Model):
    __tablename__ = 'classes'

    id = db.Column(db.Integer,primary_key=True)
    class_name = db.Column(db.String(50),nullable=False)
    section = db.Column(db.String(10),nullable=False)


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)
    roll_no = db.Column(db.String(20),unique=True,nullable=False)
    name = db.Column(db.String(100),nullable=False)
    class_id = db.Column(db.Integer,db.ForeignKey('classes.id'),nullable=False)


class Teacher(db.Model):

    __tablename__ = 'teachers'

    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False,unique=True)
    name = db.Column(db.String(100),nullable=False)
    employee_id = db.Column(db.String(30),unique=True,nullable=False)
    department = db.Column(db.String(100))


class Subject(db.Model):

    __tablename__ = 'subjects'

    id = db.Column(db.Integer,primary_key=True)
    subject_name = db.Column(db.String(100),nullable=False)
    subject_code = db.Column(db.String(30),unique=True,nullable=False)
    teacher_id = db.Column(db.Integer,db.ForeignKey('teachers.id'),nullable=False)
    class_id = db.Column(db.Integer,db.ForeignKey('classes.id'),nullable=False)

class Attendance(db.Model):

    __tablename__ = 'attendance'

    id = db.Column(db.Integer,primary_key=True)
    student_id = db.Column(db.Integer,db.ForeignKey('students.id'),nullable=False)
    subject_id = db.Column(db.Integer,db.ForeignKey('subjects.id'),nullable=False)
    teacher_id = db.Column(db.Integer,db.ForeignKey('teachers.id'),nullable=False)
    class_id = db.Column(db.Integer,db.ForeignKey('classes.id'),nullable=False)
    date = db.Column(db.Date,nullable=False)
    status = db.Column(db.String(10),nullable=False)