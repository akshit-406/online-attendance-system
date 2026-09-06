from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from models import User, Class, Student, Teacher, Subject, Attendance, db 
from datetime import datetime, date

# Create Blueprint
main = Blueprint('main', __name__)


# --------------------------------
# Home
# --------------------------------

@main.route('/')
def home():

    return redirect(
        url_for('main.login')
    )


# --------------------------------
# Login
# --------------------------------

@main.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(
            email=email
        ).first()

        if user and user.check_password(password):

            login_user(user)

            flash('Login successful!')

            return redirect(
                url_for('main.dashboard')
            )

        flash('Invalid email or password.')

    return render_template('login.html')


# --------------------------------
# Logout
# --------------------------------

@main.route('/logout')
@login_required
def logout():

    logout_user()

    flash('You have been logged out.')

    return redirect(
        url_for('main.login')
    )


# --------------------------------
# Dashboard
# --------------------------------

@main.route('/dashboard')
@login_required
def dashboard():

    if current_user.role == 'admin':

        return redirect(
            url_for('main.admin_dashboard')
        )

    elif current_user.role == 'teacher':

        return redirect(
            url_for('main.teacher_dashboard')
        )

    elif current_user.role == 'student':

        return redirect(
            url_for('main.student_dashboard')
        )

    return 'Invalid user role'


# --------------------------------
# Admin Dashboard
# --------------------------------


@main.route('/admin/dashboard')
@login_required
def admin_dashboard():

    if current_user.role != 'admin':
        return 'Access Denied', 403

    # Basic counts
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_classes = Class.query.count()
    total_subjects = Subject.query.count()

    # Attendance counts
    total_attendance = Attendance.query.count()

    present_count = Attendance.query.filter_by(
        status='Present'
    ).count()

    absent_count = Attendance.query.filter_by(
        status='Absent'
    ).count()

    # Overall attendance percentage
    if total_attendance > 0:
        attendance_percentage = (
            present_count / total_attendance
        ) * 100
    else:
        attendance_percentage = 0

    return render_template(
        'admin/dashboard.html',

        total_students=total_students,
        total_teachers=total_teachers,
        total_classes=total_classes,
        total_subjects=total_subjects,

        total_attendance=total_attendance,
        present_count=present_count,
        absent_count=absent_count,
        attendance_percentage=attendance_percentage
    )


# --------------------------------
# Teacher Dashboard
# --------------------------------


@main.route('/teacher/dashboard')
@login_required
def teacher_dashboard():

    if current_user.role != 'teacher':
        return 'Access Denied', 403

    teacher = Teacher.query.filter_by(
        user_id=current_user.id
    ).first()

    if not teacher:
        return 'Teacher profile not found', 404

    subjects = Subject.query.filter_by(
        teacher_id=teacher.id
    ).all()

    # Get class information for each subject
    subject_data = []

    for subject in subjects:

        class_item = Class.query.get(
            subject.class_id
        )

        subject_data.append({
            'subject': subject,
            'class_item': class_item
        })

    return render_template(
        'teacher/dashboard.html',
        teacher=teacher,
        subjects=subjects,
        subject_data=subject_data
    )


# --------------------------------
# Student Dashboard
# --------------------------------


@main.route('/student/dashboard')
@login_required
def student_dashboard():

    if current_user.role != 'student':
        return 'Access Denied', 403

    student = Student.query.filter_by(
        user_id=current_user.id
    ).first()

    if not student:
        return 'Student profile not found', 404

    # Get student's class information
    student_class = Class.query.get(student.class_id)

    # Get attendance records
    attendance_records = Attendance.query.filter_by(
        student_id=student.id
    ).order_by(
        Attendance.date.desc()
    ).all()

    attendance_history = []

    for record in attendance_records:

        subject = Subject.query.get(record.subject_id)

        attendance_history.append({
            'record': record,
            'subject': subject
        })

    # Attendance statistics
    total_classes = len(attendance_records)

    present_classes = sum(
        1 for record in attendance_records
        if record.status == 'Present'
    )

    absent_classes = sum(
        1 for record in attendance_records
        if record.status == 'Absent'
    )

    attendance_percentage = (
        (present_classes / total_classes) * 100
        if total_classes > 0
        else 0
    )

    return render_template(
        'student/dashboard.html',
        student=student,
        student_class=student_class,
        attendance_records=attendance_records,
        attendance_history=attendance_history,
        total_classes=total_classes,
        present_classes=present_classes,
        absent_classes=absent_classes,
        attendance_percentage=attendance_percentage
    )


@main.route('/student/attendance')
@login_required
def student_attendance():

    if current_user.role != 'student':
        return 'Access Denied', 403

    student = Student.query.filter_by(
        user_id=current_user.id
    ).first()

    if not student:
        return 'Student profile not found', 404

    # Get all attendance records of student
    attendance_records = Attendance.query.filter_by(
        student_id=student.id
    ).order_by(
        Attendance.date.desc()
    ).all()

    attendance_history = []

    for record in attendance_records:

        subject = Subject.query.get(record.subject_id)

        attendance_history.append({
            'record': record,
            'subject': subject
        })

    # Get class information
    student_class = Class.query.get(student.class_id)

    # Subject-wise attendance
    subject_reports = {}

    for record in attendance_records:

        subject = Subject.query.get(record.subject_id)

        if subject.id not in subject_reports:
            subject_reports[subject.id] = {
                'subject': subject,
                'total': 0,
                'present': 0,
                'absent': 0
            }

        subject_reports[subject.id]['total'] += 1

        if record.status == 'Present':
            subject_reports[subject.id]['present'] += 1

        elif record.status == 'Absent':
            subject_reports[subject.id]['absent'] += 1

    # Calculate percentage
    for report in subject_reports.values():

        if report['total'] > 0:
            report['percentage'] = (
                report['present'] / report['total']
            ) * 100
        else:
            report['percentage'] = 0

    return render_template(
        'student/attendance.html',
        student=student,
        student_class=student_class,
        attendance_records=attendance_records,
        attendance_history=attendance_history,
        subject_reports=subject_reports.values()
    )

# --------------------------------
# Manage Classes
# --------------------------------


@main.route('/admin/classes')
@login_required
def manage_classes():

    if current_user.role != 'admin':
        return 'Access Denied', 403

    classes = Class.query.order_by(
        Class.class_name,
        Class.section
    ).all()

    return render_template(
        'admin/classes.html',
        classes=classes
    )


# --------------------------------
# Add Class
# --------------------------------


@main.route('/admin/classes/add', methods=['GET', 'POST'])
@login_required
def add_class():

    if current_user.role != 'admin':
        return 'Access Denied', 403

    if request.method == 'POST':

        class_name = request.form.get('class_name', '').strip()
        section = request.form.get('section', '').strip()

        # Validation
        if not class_name or not section:

            flash('Class name and section are required.')

            return render_template(
                'admin/add_class.html'
            )

        # Check duplicate class + section
        existing_class = Class.query.filter_by(
            class_name=class_name,
            section=section
        ).first()

        if existing_class:

            flash(
                'This class and section already exists.'
            )

            return render_template(
                'admin/add_class.html'
            )

        # Create class
        new_class = Class(
            class_name=class_name,
            section=section
        )

        db.session.add(new_class)
        db.session.commit()

        flash('Class added successfully!')

        return redirect(
            url_for('main.manage_classes')
        )

    return render_template(
        'admin/add_class.html'
    )


# --------------------------------
# Edit Class
# --------------------------------


@main.route(
    '/admin/classes/edit/<int:class_id>',
    methods=['GET', 'POST']
)
@login_required
def edit_class(class_id):

    if current_user.role != 'admin':
        return 'Access Denied', 403

    class_item = Class.query.get_or_404(class_id)

    if request.method == 'POST':

        class_name = request.form.get(
            'class_name', ''
        ).strip()

        section = request.form.get(
            'section', ''
        ).strip()

        # Validation
        if not class_name or not section:

            flash(
                'Class name and section are required.'
            )

            return render_template(
                'admin/edit_class.html',
                class_item=class_item
            )

        # Check duplicate class + section
        existing_class = Class.query.filter(
            Class.class_name == class_name,
            Class.section == section,
            Class.id != class_item.id
        ).first()

        if existing_class:

            flash(
                'This class and section already exists.'
            )

            return render_template(
                'admin/edit_class.html',
                class_item=class_item
            )

        class_item.class_name = class_name
        class_item.section = section

        db.session.commit()

        flash('Class updated successfully!')

        return redirect(
            url_for('main.manage_classes')
        )

    return render_template(
        'admin/edit_class.html',
        class_item=class_item
    )


# --------------------------------
# Delete Class
# --------------------------------


@main.route(
    '/admin/classes/delete/<int:class_id>',
    methods=['POST']
)
@login_required
def delete_class(class_id):

    if current_user.role != 'admin':
        return 'Access Denied', 403

    class_item = Class.query.get_or_404(class_id)

    # Check students
    student_count = Student.query.filter_by(
        class_id=class_item.id
    ).count()

    if student_count > 0:

        flash(
            'This class cannot be deleted because '
            'students are assigned to it.'
        )

        return redirect(
            url_for('main.manage_classes')
        )

    # Check subjects
    subject_count = Subject.query.filter_by(
        class_id=class_item.id
    ).count()

    if subject_count > 0:

        flash(
            'This class cannot be deleted because '
            'subjects are assigned to it.'
        )

        return redirect(
            url_for('main.manage_classes')
        )

    # Check attendance records
    attendance_count = Attendance.query.filter_by(
        class_id=class_item.id
    ).count()

    if attendance_count > 0:

        flash(
            'This class cannot be deleted because '
            'attendance records exist for it.'
        )

        return redirect(
            url_for('main.manage_classes')
        )

    # Safe to delete
    db.session.delete(class_item)

    db.session.commit()

    flash('Class deleted successfully!')

    return redirect(
        url_for('main.manage_classes')
    )


# --------------------------------
# Manage Students
# --------------------------------


@main.route('/admin/students')
@login_required
def manage_students():
    if current_user.role != 'admin':
        return 'Access Denied', 403

    students = Student.query.all()

    student_data = []

    for student in students:
        user = User.query.get(student.user_id)
        class_item = Class.query.get(student.class_id)

        student_data.append({
            'student': student,
            'user': user,
            'class_item': class_item
        })

    return render_template(
        'admin/students.html',
        student_data=student_data
    )


# --------------------------------
# Add Student
# --------------------------------


@main.route('/admin/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if current_user.role != 'admin':
        return 'Access Denied', 403

    student_users = User.query.filter_by(
        role='student'
    ).order_by(User.username).all()

    existing_student_user_ids = {
        student.user_id for student in Student.query.all()
    }

    available_users = [
        user for user in student_users
        if user.id not in existing_student_user_ids
    ]

    classes = Class.query.order_by(
        Class.class_name,
        Class.section
    ).all()

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        name = request.form.get('name', '').strip()
        roll_no = request.form.get('roll_no', '').strip()
        class_id = request.form.get('class_id')

        if not user_id or not name or not roll_no or not class_id:
            flash('All fields are required.')
            return render_template(
                'admin/add_student.html',
                available_users=available_users,
                classes=classes
            )

        user = User.query.get(user_id)

        if not user or user.role != 'student':
            flash('Invalid student user selected.')
            return render_template(
                'admin/add_student.html',
                available_users=available_users,
                classes=classes
            )

        existing_student = Student.query.filter_by(
            user_id=user.id
        ).first()

        if existing_student:
            flash('This user already has a student profile.')
            return render_template(
                'admin/add_student.html',
                available_users=available_users,
                classes=classes
            )

        existing_roll = Student.query.filter_by(
            roll_no=roll_no
        ).first()

        if existing_roll:
            flash('Roll number already exists.')
            return render_template(
                'admin/add_student.html',
                available_users=available_users,
                classes=classes
            )

        class_item = Class.query.get(class_id)

        if not class_item:
            flash('Invalid class selected.')
            return render_template(
                'admin/add_student.html',
                available_users=available_users,
                classes=classes
            )

        student = Student(
            user_id=user.id,
            name=name,
            roll_no=roll_no,
            class_id=class_item.id
        )

        db.session.add(student)
        db.session.commit()

        flash('Student added successfully!')
        return redirect(url_for('main.manage_students'))

    return render_template(
        'admin/add_student.html',
        available_users=available_users,
        classes=classes
    )


# --------------------------------
# Edit Student
# --------------------------------


@main.route('/admin/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    if current_user.role != 'admin':
        return 'Access Denied', 403

    student = Student.query.get_or_404(student_id)

    user = User.query.get(student.user_id)

    classes = Class.query.order_by(
        Class.class_name,
        Class.section
    ).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        roll_no = request.form.get('roll_no', '').strip()
        class_id = request.form.get('class_id')

        if not name or not roll_no or not class_id:
            flash('All fields are required.')
            return render_template(
                'admin/edit_student.html',
                student=student,
                user=user,
                classes=classes
            )

        existing_roll = Student.query.filter(
            Student.roll_no == roll_no,
            Student.id != student.id
        ).first()

        if existing_roll:
            flash('Roll number already exists.')
            return render_template(
                'admin/edit_student.html',
                student=student,
                user=user,
                classes=classes
            )

        class_item = Class.query.get(class_id)

        if not class_item:
            flash('Invalid class selected.')
            return render_template(
                'admin/edit_student.html',
                student=student,
                user=user,
                classes=classes
            )

        student.name = name
        student.roll_no = roll_no
        student.class_id = class_item.id

        db.session.commit()

        flash('Student updated successfully!')
        return redirect(url_for('main.manage_students'))

    return render_template(
        'admin/edit_student.html',
        student=student,
        user=user,
        classes=classes
    )


# --------------------------------
# Delete Student
# --------------------------------


@main.route('/admin/students/delete/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    if current_user.role != 'admin':
        return 'Access Denied', 403

    student = Student.query.get_or_404(student_id)

    # Check whether attendance records exist
    attendance_count = Attendance.query.filter_by(
        student_id=student.id
    ).count()

    if attendance_count > 0:
        flash(
            'This student cannot be deleted because attendance records exist for them.'
        )
        return redirect(url_for('main.manage_students'))

    # Save the related login user ID
    user_id = student.user_id

    # Delete student profile
    db.session.delete(student)
    db.session.commit()

    flash('Student profile deleted successfully!')

    return redirect(url_for('main.manage_students'))


# --------------------------------
# Manage Teachers
# --------------------------------


@main.route('/admin/teachers')
@login_required
def manage_teachers():

    if current_user.role != 'admin':
        return 'Access Denied', 403

    teachers = Teacher.query.all()

    return render_template(
        'admin/teachers.html',
        teachers=teachers
    )


# --------------------------------
# Add Teacher
# --------------------------------


@main.route('/admin/teachers/add', methods=['GET', 'POST'])
@login_required
def add_teacher():
    if current_user.role != 'admin':
        return 'Access Denied', 403

    teacher_users = User.query.filter_by(role='teacher').order_by(User.username).all()

    existing_teacher_user_ids = {
        teacher.user_id for teacher in Teacher.query.all()
    }

    available_users = [
        user for user in teacher_users
        if user.id not in existing_teacher_user_ids
    ]

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        name = request.form.get('name', '').strip()
        employee_id = request.form.get('employee_id', '').strip()
        department = request.form.get('department', '').strip()

        if not user_id or not name or not employee_id:
            flash('User, name and Employee ID are required.')
            return render_template(
                'admin/add_teacher.html',
                available_users=available_users
            )

        user = User.query.get(user_id)

        if not user or user.role != 'teacher':
            flash('Invalid teacher user selected.')
            return render_template(
                'admin/add_teacher.html',
                available_users=available_users
            )

        existing_teacher = Teacher.query.filter_by(user_id=user.id).first()

        if existing_teacher:
            flash('This user already has a teacher profile.')
            return render_template(
                'admin/add_teacher.html',
                available_users=available_users
            )

        existing_employee = Teacher.query.filter_by(
            employee_id=employee_id
        ).first()

        if existing_employee:
            flash('Employee ID already exists.')
            return render_template(
                'admin/add_teacher.html',
                available_users=available_users
            )

        teacher = Teacher(
            user_id=user.id,
            name=name,
            employee_id=employee_id,
            department=department
        )

        db.session.add(teacher)
        db.session.commit()

        flash('Teacher added successfully!')
        return redirect(url_for('main.manage_teachers'))

    return render_template(
        'admin/add_teacher.html',
        available_users=available_users
    )


# --------------------------------
# Edit Teacher
# --------------------------------


@main.route('/admin/teachers/edit/<int:teacher_id>', methods=['GET', 'POST'])
@login_required
def edit_teacher(teacher_id):
    if current_user.role != 'admin':
        return 'Access Denied', 403

    teacher = Teacher.query.get_or_404(teacher_id)

    teacher_users = User.query.filter_by(
        role='teacher'
    ).order_by(User.username).all()

    if request.method == 'POST':

        user_id = request.form.get('user_id')
        name = request.form.get('name', '').strip()
        employee_id = request.form.get('employee_id', '').strip()
        department = request.form.get('department', '').strip()

        if not user_id or not name or not employee_id:
            flash('User, name and Employee ID are required.')

            return render_template(
                'admin/edit_teacher.html',
                teacher=teacher,
                teacher_users=teacher_users
            )

        user = User.query.get(user_id)

        if not user or user.role != 'teacher':
            flash('Invalid teacher user selected.')

            return render_template(
                'admin/edit_teacher.html',
                teacher=teacher,
                teacher_users=teacher_users
            )

        # Check whether another teacher is using this User account

        existing_user_teacher = Teacher.query.filter(
            Teacher.user_id == user.id,
            Teacher.id != teacher.id
        ).first()

        if existing_user_teacher:
            flash('This user account is already assigned to another teacher.')

            return render_template(
                'admin/edit_teacher.html',
                teacher=teacher,
                teacher_users=teacher_users
            )

        # Check duplicate Employee ID

        existing_employee = Teacher.query.filter(
            Teacher.employee_id == employee_id,
            Teacher.id != teacher.id
        ).first()

        if existing_employee:
            flash('Employee ID already exists.')

            return render_template(
                'admin/edit_teacher.html',
                teacher=teacher,
                teacher_users=teacher_users
            )

        teacher.user_id = user.id
        teacher.name = name
        teacher.employee_id = employee_id
        teacher.department = department

        db.session.commit()

        flash('Teacher updated successfully!')

        return redirect(url_for('main.manage_teachers'))

    return render_template(
        'admin/edit_teacher.html',
        teacher=teacher,
        teacher_users=teacher_users
    )


# --------------------------------
# Delete Teacher
# --------------------------------


@main.route('/admin/teachers/delete/<int:teacher_id>', methods=['POST'])
@login_required
def delete_teacher(teacher_id):
    if current_user.role != 'admin':
        return 'Access Denied', 403

    teacher = Teacher.query.get_or_404(teacher_id)

    # Check for subjects assigned to this teacher
    subject_count = Subject.query.filter_by(
        teacher_id=teacher.id
    ).count()

    if subject_count > 0:
        flash(
            'This teacher cannot be deleted because subjects are assigned to them.'
        )
        return redirect(url_for('main.manage_teachers'))

    # Check for attendance records
    attendance_count = Attendance.query.filter_by(
        teacher_id=teacher.id
    ).count()

    if attendance_count > 0:
        flash(
            'This teacher cannot be deleted because attendance records exist for them.'
        )
        return redirect(url_for('main.manage_teachers'))

    # Save the associated user ID before deleting the teacher
    user_id = teacher.user_id

    db.session.delete(teacher)
    db.session.commit()

    flash('Teacher profile deleted successfully!')

    return redirect(url_for('main.manage_teachers'))


# --------------------------------
# Manage Subjects
# --------------------------------


@main.route('/admin/subjects')
@login_required
def manage_subjects():
    if current_user.role != 'admin':
        return 'Access Denied', 403

    subjects = Subject.query.all()

    subject_data = []

    for subject in subjects:
        teacher = Teacher.query.get(subject.teacher_id)
        class_item = Class.query.get(subject.class_id)

        subject_data.append({
            'subject': subject,
            'teacher': teacher,
            'class_item': class_item
        })

    return render_template(
        'admin/subjects.html',
        subject_data=subject_data
    )


# --------------------------------
# Add Subject
# --------------------------------


@main.route('/admin/subjects/add', methods=['GET', 'POST'])
@login_required
def add_subject():
    if current_user.role != 'admin':
        return 'Access Denied', 403

    teachers = Teacher.query.order_by(Teacher.name).all()
    classes = Class.query.order_by(
        Class.class_name,
        Class.section
    ).all()

    if request.method == 'POST':

        subject_name = request.form.get('subject_name', '').strip()
        subject_code = request.form.get('subject_code', '').strip()
        teacher_id = request.form.get('teacher_id')
        class_id = request.form.get('class_id')

        if not subject_name or not subject_code or not teacher_id or not class_id:
            flash('All fields are required.')

            return render_template(
                'admin/add_subject.html',
                teachers=teachers,
                classes=classes
            )

        # Check teacher
        teacher = Teacher.query.get(teacher_id)

        if not teacher:
            flash('Invalid teacher selected.')

            return render_template(
                'admin/add_subject.html',
                teachers=teachers,
                classes=classes
            )

        # Check class
        class_item = Class.query.get(class_id)

        if not class_item:
            flash('Invalid class selected.')

            return render_template(
                'admin/add_subject.html',
                teachers=teachers,
                classes=classes
            )

        # Check duplicate subject code
        existing_subject = Subject.query.filter_by(
            subject_code=subject_code
        ).first()

        if existing_subject:
            flash('Subject code already exists.')

            return render_template(
                'admin/add_subject.html',
                teachers=teachers,
                classes=classes
            )

        # Create subject
        subject = Subject(
            subject_name=subject_name,
            subject_code=subject_code,
            teacher_id=teacher.id,
            class_id=class_item.id
        )

        db.session.add(subject)
        db.session.commit()

        flash('Subject added successfully!')

        return redirect(url_for('main.manage_subjects'))

    return render_template(
        'admin/add_subject.html',
        teachers=teachers,
        classes=classes
    )


# --------------------------------
# Edit Subject
# --------------------------------


@main.route('/admin/subjects/edit/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    if current_user.role != 'admin':
        return 'Access Denied', 403

    subject = Subject.query.get_or_404(subject_id)

    teachers = Teacher.query.order_by(Teacher.name).all()
    classes = Class.query.order_by(
        Class.class_name,
        Class.section
    ).all()

    if request.method == 'POST':

        subject_name = request.form.get('subject_name', '').strip()
        subject_code = request.form.get('subject_code', '').strip()
        teacher_id = request.form.get('teacher_id')
        class_id = request.form.get('class_id')

        if not subject_name or not subject_code or not teacher_id or not class_id:
            flash('All fields are required.')

            return render_template(
                'admin/edit_subject.html',
                subject=subject,
                teachers=teachers,
                classes=classes
            )

        teacher = Teacher.query.get(teacher_id)

        if not teacher:
            flash('Invalid teacher selected.')

            return render_template(
                'admin/edit_subject.html',
                subject=subject,
                teachers=teachers,
                classes=classes
            )

        class_item = Class.query.get(class_id)

        if not class_item:
            flash('Invalid class selected.')

            return render_template(
                'admin/edit_subject.html',
                subject=subject,
                teachers=teachers,
                classes=classes
            )

        # Check duplicate subject code
        existing_subject = Subject.query.filter(
            Subject.subject_code == subject_code,
            Subject.id != subject.id
        ).first()

        if existing_subject:
            flash('Subject code already exists.')

            return render_template(
                'admin/edit_subject.html',
                subject=subject,
                teachers=teachers,
                classes=classes
            )

        subject.subject_name = subject_name
        subject.subject_code = subject_code
        subject.teacher_id = teacher.id
        subject.class_id = class_item.id

        db.session.commit()

        flash('Subject updated successfully!')

        return redirect(url_for('main.manage_subjects'))

    return render_template(
        'admin/edit_subject.html',
        subject=subject,
        teachers=teachers,
        classes=classes
    )


# --------------------------------
# Manage Users
# --------------------------------


@main.route('/admin/users')
@login_required
def manage_users():

    if current_user.role != 'admin':
        return 'Access Denied', 403

    users = User.query.order_by(
        User.id
    ).all()

    return render_template(
        'admin/users.html',
        users=users
    )


@main.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
def add_user():

    if current_user.role != 'admin':
        return 'Access Denied', 403

    if request.method == 'POST':

        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        # Basic validation
        if not username or not email or not password or not role:

            flash('Please fill all fields.')

            return render_template(
                'admin/add_user.html'
            )

        # Validate role
        if role not in ['admin', 'teacher', 'student']:

            flash('Invalid role selected.')

            return render_template(
                'admin/add_user.html'
            )

        # Check duplicate username
        existing_username = User.query.filter_by(
            username=username
        ).first()

        if existing_username:

            flash('Username already exists.')

            return render_template(
                'admin/add_user.html'
            )

        # Check duplicate email
        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:

            flash('Email already exists.')

            return render_template(
                'admin/add_user.html'
            )

        # Create User
        user = User(
            username=username,
            email=email,
            role=role
        )

        user.set_password(password)

        db.session.add(user)

        db.session.commit()

        # --------------------------------
        # Redirect according to role
        # --------------------------------

        if role == 'student':

            flash(
                'Student login account created. '
                'Please complete the student profile.'
            )

            return redirect(
                url_for(
                    'main.complete_student_profile',
                    user_id=user.id
                )
            )

        elif role == 'teacher':

            flash(
                'Teacher login account created. '
                'Please complete the teacher profile.'
            )

            return redirect(
                url_for(
                    'main.complete_teacher_profile',
                    user_id=user.id
                )
            )

        else:

            flash('Admin user created successfully!')

            return redirect(
                url_for('main.manage_users')
            )

    return render_template(
        'admin/add_user.html'
    )


# --------------------------------
# Complete Student Profile
# --------------------------------


@main.route(
    '/admin/users/<int:user_id>/student-profile',
    methods=['GET', 'POST']
)
@login_required
def complete_student_profile(user_id):

    if current_user.role != 'admin':
        return 'Access Denied', 403

    user = User.query.get_or_404(user_id)

    # Make sure this user is a student
    if user.role != 'student':
        return 'Invalid user role', 400

    # Check if profile already exists
    existing_student = Student.query.filter_by(
        user_id=user.id
    ).first()

    if existing_student:

        flash('Student profile already exists.')

        return redirect(
            url_for('main.manage_students')
        )

    classes = Class.query.order_by(
        Class.class_name,
        Class.section
    ).all()

    if request.method == 'POST':

        name = request.form.get('name')
        roll_no = request.form.get('roll_no')
        class_id = request.form.get('class_id')

        # Validation
        if not name or not roll_no or not class_id:

            flash('Please fill all fields.')

            return render_template(
                'admin/complete_student_profile.html',
                user=user,
                classes=classes
            )

        # Check duplicate roll number
        existing_student = Student.query.filter_by(
            roll_no=roll_no
        ).first()

        if existing_student:

            flash('Roll number already exists.')

            return render_template(
                'admin/complete_student_profile.html',
                user=user,
                classes=classes
            )

        # Create Student profile
        student = Student(
            user_id=user.id,
            roll_no=roll_no,
            name=name,
            class_id=class_id
        )

        db.session.add(student)

        db.session.commit()

        flash('Student profile created successfully!')

        return redirect(
            url_for('main.manage_students')
        )

    return render_template(
        'admin/complete_student_profile.html',
        user=user,
        classes=classes
    )


# --------------------------------
# Complete Teacher Profile
# --------------------------------


@main.route(
    '/admin/users/<int:user_id>/teacher-profile',
    methods=['GET', 'POST']
)
@login_required
def complete_teacher_profile(user_id):

    if current_user.role != 'admin':
        return 'Access Denied', 403

    user = User.query.get_or_404(user_id)

    # Make sure this user is a teacher
    if user.role != 'teacher':
        return 'Invalid user role', 400

    # Check if profile already exists
    existing_teacher = Teacher.query.filter_by(
        user_id=user.id
    ).first()

    if existing_teacher:

        flash('Teacher profile already exists.')

        return redirect(
            url_for('main.manage_teachers')
        )

    if request.method == 'POST':

        name = request.form.get('name')
        employee_id = request.form.get('employee_id')
        department = request.form.get('department')

        # Validation
        if not name or not employee_id:

            flash(
                'Name and Employee ID are required.'
            )

            return render_template(
                'admin/complete_teacher_profile.html',
                user=user
            )

        # Check duplicate employee ID
        existing_teacher = Teacher.query.filter_by(
            employee_id=employee_id
        ).first()

        if existing_teacher:

            flash('Employee ID already exists.')

            return render_template(
                'admin/complete_teacher_profile.html',
                user=user
            )

        # Create Teacher profile
        teacher = Teacher(
            user_id=user.id,
            name=name,
            employee_id=employee_id,
            department=department
        )

        db.session.add(teacher)

        db.session.commit()

        flash('Teacher profile created successfully!')

        return redirect(
            url_for('main.manage_teachers')
        )

    return render_template(
        'admin/complete_teacher_profile.html',
        user=user
    )




    if current_user.role != 'admin':
        return 'Access Denied', 403

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':

        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if not username or not email or not role:
            flash('Username, email and role are required.')
            return render_template(
                'admin/edit_user.html',
                user=user
            )

        if role not in ['admin', 'teacher', 'student']:
            flash('Invalid role selected.')
            return render_template(
                'admin/edit_user.html',
                user=user
            )

        # Check duplicate username
        existing_username = User.query.filter(
            User.username == username,
            User.id != user.id
        ).first()

        if existing_username:
            flash('Username already exists.')
            return render_template(
                'admin/edit_user.html',
                user=user
            )

        # Check duplicate email
        existing_email = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()

        if existing_email:
            flash('Email already exists.')
            return render_template(
                'admin/edit_user.html',
                user=user
            )

        user.username = username
        user.email = email
        user.role = role

        # Change password only if entered
        if password:
            user.set_password(password)

        db.session.commit()

        flash('User updated successfully!')

        return redirect(
            url_for('main.manage_users')
        )

    return render_template(
        'admin/edit_user.html',
        user=user
    )


@main.route(
    '/admin/users/edit/<int:user_id>',
    methods=['GET', 'POST']
)
@login_required
def edit_user(user_id):

    if current_user.role != 'admin':
        return 'Access Denied', 403

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':

        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        new_role = request.form.get('role')

        # --------------------------------
        # Basic validation
        # --------------------------------

        if not username or not email or not new_role:

            flash('Username, email and role are required.')

            return render_template(
                'admin/edit_user.html',
                user=user
            )

        if new_role not in ['admin', 'teacher', 'student']:

            flash('Invalid role selected.')

            return render_template(
                'admin/edit_user.html',
                user=user
            )

        # --------------------------------
        # Check duplicate username
        # --------------------------------

        existing_username = User.query.filter(
            User.username == username,
            User.id != user.id
        ).first()

        if existing_username:

            flash('Username already exists.')

            return render_template(
                'admin/edit_user.html',
                user=user
            )

        # --------------------------------
        # Check duplicate email
        # --------------------------------

        existing_email = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()

        if existing_email:

            flash('Email already exists.')

            return render_template(
                'admin/edit_user.html',
                user=user
            )

        # --------------------------------
        # Prevent unsafe role changes
        # --------------------------------

        if new_role != user.role:

            # Student profile exists
            student = Student.query.filter_by(
                user_id=user.id
            ).first()

            # Teacher profile exists
            teacher = Teacher.query.filter_by(
                user_id=user.id
            ).first()

            if student or teacher:

                flash(
                    'Role cannot be changed because this user '
                    'already has a profile. Please manage the '
                    'student/teacher profile separately.'
                )

                return render_template(
                    'admin/edit_user.html',
                    user=user
                )

        # --------------------------------
        # Update User
        # --------------------------------

        user.username = username
        user.email = email
        user.role = new_role

        # Change password only if entered
        if password:

            user.set_password(password)

        db.session.commit()

        flash('User updated successfully!')

        return redirect(
            url_for('main.manage_users')
        )

    return render_template(
        'admin/edit_user.html',
        user=user
    )


@main.route(
    '/admin/users/delete/<int:user_id>',
    methods=['POST']
)
@login_required
def delete_user(user_id):

    if current_user.role != 'admin':
        return 'Access Denied', 403

    user = User.query.get_or_404(user_id)

    # --------------------------------
    # Prevent self deletion
    # --------------------------------

    if user.id == current_user.id:

        flash(
            'You cannot delete your own account.'
        )

        return redirect(
            url_for('main.manage_users')
        )

    # --------------------------------
    # Check Student profile
    # --------------------------------

    student = Student.query.filter_by(
        user_id=user.id
    ).first()

    if student:

        flash(
            'This user has a student profile. '
            'Delete the student from Manage Students first.'
        )

        return redirect(
            url_for('main.manage_users')
        )

    # --------------------------------
    # Check Teacher profile
    # --------------------------------

    teacher = Teacher.query.filter_by(
        user_id=user.id
    ).first()

    if teacher:

        flash(
            'This user has a teacher profile. '
            'Delete the teacher from Manage Teachers first.'
        )

        return redirect(
            url_for('main.manage_users')
        )

    # --------------------------------
    # Delete User
    # --------------------------------

    db.session.delete(user)

    db.session.commit()

    flash('User deleted successfully!')

    return redirect(
        url_for('main.manage_users')
    )


# --------------------------------
# Delete Subject
# --------------------------------


@main.route('/admin/subjects/delete/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    if current_user.role != 'admin':
        return 'Access Denied', 403

    subject = Subject.query.get_or_404(subject_id)

    # Check whether attendance records exist
    attendance_count = Attendance.query.filter_by(
        subject_id=subject.id
    ).count()

    if attendance_count > 0:
        flash(
            'This subject cannot be deleted because attendance records exist for it.'
        )
        return redirect(url_for('main.manage_subjects'))

    db.session.delete(subject)
    db.session.commit()

    flash('Subject deleted successfully!')

    return redirect(url_for('main.manage_subjects'))


# --------------------------------
# Mark Attendance
# --------------------------------


@main.route(
    '/teacher/attendance/<int:subject_id>',
    methods=['GET', 'POST']
)
@login_required
def mark_attendance(subject_id):

    if current_user.role != 'teacher':
        return 'Access Denied', 403

    # Find logged-in teacher
    teacher = Teacher.query.filter_by(
        user_id=current_user.id
    ).first()

    if not teacher:
        return 'Teacher profile not found', 404

    # Find subject
    subject = Subject.query.get_or_404(
        subject_id
    )

    student_class = Class.query.get(
        subject.class_id
    )

    # Make sure subject belongs to teacher
    if subject.teacher_id != teacher.id:
        return 'Access Denied', 403

    # Get students of this class
    students = Student.query.filter_by(
        class_id=subject.class_id
    ).order_by(
        Student.roll_no
    ).all()

    # Today's date
    today = date.today()

    if request.method == 'POST':

        # Get date from form
        attendance_date = request.form.get(
            'attendance_date'
        )

        # Validate date
        if not attendance_date:

            flash('Please select a date.')

            return render_template(
                'teacher/mark_attendance.html',
                subject=subject,
                students=students,
                today=today,
                student_class=student_class
            )

        # Convert string to Python date
        try:

            attendance_date = datetime.strptime(
                attendance_date,
                '%Y-%m-%d'
            ).date()

        except ValueError:

            flash('Invalid date selected.')

            return render_template(
                'teacher/mark_attendance.html',
                subject=subject,
                students=students,
                today=today,
                student_class=student_class
            )

        # Prevent future attendance
        if attendance_date > today:

            flash(
                'Attendance cannot be marked for a future date.'
            )

            return render_template(
                'teacher/mark_attendance.html',
                subject=subject,
                students=students,
                today=today,
                student_class=student_class
            )

        # Make sure students exist
        if not students:

            flash(
                'No students are assigned to this class.'
            )

            return render_template(
                'teacher/mark_attendance.html',
                subject=subject,
                students=students,
                today=today,
                student_class=student_class
            )

        saved_count = 0
        updated_count = 0

        # Process every student
        for student in students:

            status = request.form.get(
                f'status_{student.id}'
            )

            # Ignore invalid status
            if status not in ['Present', 'Absent']:
                continue

            # Check existing attendance
            existing = Attendance.query.filter_by(
                student_id=student.id,
                subject_id=subject.id,
                date=attendance_date
            ).first()

            if existing:

                # Update existing record
                existing.status = status
                existing.teacher_id = teacher.id
                existing.class_id = subject.class_id

                updated_count += 1

            else:

                # Create new record
                attendance = Attendance(
                    student_id=student.id,
                    subject_id=subject.id,
                    teacher_id=teacher.id,
                    class_id=subject.class_id,
                    date=attendance_date,
                    status=status
                )

                db.session.add(attendance)

                saved_count += 1

        # Nothing was submitted
        if saved_count == 0 and updated_count == 0:

            flash(
                'No attendance records were selected.'
            )

            return render_template(
                'teacher/mark_attendance.html',
                subject=subject,
                students=students,
                today=today,
                student_class=student_class
            )

        # Save changes
        db.session.commit()

        # Success message
        if saved_count > 0 and updated_count > 0:

            flash(
                f'{saved_count} new attendance records saved '
                f'and {updated_count} records updated.'
            )

        elif saved_count > 0:

            flash(
                f'{saved_count} attendance records saved successfully!'
            )

        else:

            flash(
                f'{updated_count} attendance records updated successfully!'
            )

        return redirect(
            url_for(
                'main.teacher_dashboard'
            )
        )

    # GET request
    return render_template(
        'teacher/mark_attendance.html',
        subject=subject,
        students=students,
        today=today,
        student_class=student_class
    )


@main.route('/teacher/attendance-history')
@login_required
def teacher_attendance_history():

    if current_user.role != 'teacher':
        return 'Access Denied', 403

    teacher = Teacher.query.filter_by(
        user_id=current_user.id
    ).first()

    if not teacher:
        return 'Teacher profile not found', 404

    attendance_records = Attendance.query.filter_by(
        teacher_id=teacher.id
    ).order_by(
        Attendance.date.desc()
    ).all()

    attendance_data = []

    for record in attendance_records:

        student = Student.query.get(record.student_id)
        subject = Subject.query.get(record.subject_id)
        student_class = Class.query.get(record.class_id)

        attendance_data.append({
            'record': record,
            'student': student,
            'subject': subject,
            'class_item': student_class
        })

    return render_template(
        'teacher/attendance_history.html',
        attendance_data=attendance_data
    )

# --------------------------------
# Admin Attendance Report
# --------------------------------


@main.route('/admin/attendance')
@login_required
def admin_attendance():

    if current_user.role != 'admin':
        return 'Access Denied', 403

    # Get filter values
    class_id = request.args.get('class_id')
    subject_id = request.args.get('subject_id')
    student_id = request.args.get('student_id')
    attendance_date = request.args.get('date')
    status = request.args.get('status')

    # Get all classes
    classes = Class.query.order_by(
        Class.class_name,
        Class.section
    ).all()

    # Get all subjects
    subjects = Subject.query.order_by(
        Subject.subject_name
    ).all()

    students = Student.query.order_by(
        Student.name
    ).all()

    # Start attendance query
    query = Attendance.query

    # Filter by class
    if class_id:
        query = query.filter(
            Attendance.class_id == int(class_id)
        )

    # Filter by subject
    if subject_id:
        query = query.filter(
            Attendance.subject_id == int(subject_id)
        )

    # Filter by student
    if student_id:
        query = query.filter(
            Attendance.student_id == int(student_id)
        )    

    # Filter by date
    selected_date = None

    if attendance_date:

        selected_date = datetime.strptime(
            attendance_date,
            '%Y-%m-%d'
        ).date()

        query = query.filter(
            Attendance.date == selected_date
        )

    # Filter by status
    if status:
        query = query.filter(
            Attendance.status == status
        )

    # Get attendance records
    attendance_records = query.order_by(
        Attendance.date.desc()
    ).all()

    # Attendance summary
    total_records = len(attendance_records)

    present_count = sum(
        1 for record in attendance_records
        if record.status == 'Present'
    )

    absent_count = sum(
        1 for record in attendance_records
        if record.status == 'Absent'
    )

    # Attendance percentage
    if total_records > 0:
        attendance_percentage = (
            present_count / total_records
        ) * 100
    else:
        attendance_percentage = 0

    # --------------------------------
    # Prepare information for template
    # --------------------------------

    attendance_data = []

    for record in attendance_records:

        student = Student.query.get(
            record.student_id
        )

        subject = Subject.query.get(
            record.subject_id
        )

        teacher = Teacher.query.get(
            record.teacher_id
        )

        class_item = Class.query.get(
            record.class_id
        )

        attendance_data.append({
            'record': record,
            'student': student,
            'subject': subject,
            'teacher': teacher,
            'class_item': class_item
        })

    return render_template(
        'admin/attendance.html',
        attendance_data=attendance_data,
        classes=classes,
        subjects=subjects,
        students=students,
        selected_class_id=class_id,
        selected_subject_id=subject_id,
        selected_student_id=student_id,
        selected_date=attendance_date,
        selected_status=status,
        total_records=total_records,
        present_count=present_count,
        absent_count=absent_count,
        attendance_percentage=attendance_percentage,
    )


# --------------------------------
# Admin Student Attendance Report
# --------------------------------


@main.route('/admin/student-attendance')
@login_required
def admin_student_attendance():

    if current_user.role != 'admin':
        return 'Access Denied', 403

    # Get selected student
    student_id = request.args.get('student_id')

    # Get all students
    students = Student.query.order_by(
        Student.name
    ).all()

    selected_student = None
    subject_reports = []
    overall_total = 0
    overall_present = 0
    overall_absent = 0
    overall_percentage = 0
    selected_class = None

    if student_id:

        selected_student = Student.query.get(
            int(student_id)
        )

        selected_class = None

        if selected_student:
            selected_class = Class.query.get(
                selected_student.class_id
            )

        if selected_student:

            # Get student's attendance
            attendance_records = Attendance.query.filter_by(
                student_id=selected_student.id
            ).order_by(
                Attendance.date.desc()
            ).all()

            subject_reports_dict = {}

            for record in attendance_records:

                subject = Subject.query.get(
                    record.subject_id
                )

                if not subject:
                    continue

                if subject.id not in subject_reports_dict:

                    subject_reports_dict[subject.id] = {
                        'subject': subject,
                        'total': 0,
                        'present': 0,
                        'absent': 0
                    }

                subject_reports_dict[
                    subject.id
                ]['total'] += 1

                if record.status == 'Present':

                    subject_reports_dict[
                        subject.id
                    ]['present'] += 1

                elif record.status == 'Absent':

                    subject_reports_dict[
                        subject.id
                    ]['absent'] += 1

            # Calculate subject percentages
            for report in subject_reports_dict.values():

                if report['total'] > 0:

                    report['percentage'] = (
                        report['present']
                        / report['total']
                    ) * 100

                else:

                    report['percentage'] = 0

                overall_total += report['total']
                overall_present += report['present']
                overall_absent += report['absent']

            subject_reports = list(
                subject_reports_dict.values()
            )

            # Calculate overall percentage
            if overall_total > 0:

                overall_percentage = (
                    overall_present
                    / overall_total
                ) * 100

    return render_template(
        'admin/student_attendance.html',
        students=students,
        selected_student=selected_student,
        subject_reports=subject_reports,
        overall_total=overall_total,
        overall_present=overall_present,
        overall_absent=overall_absent,
        overall_percentage=overall_percentage,
        selected_student_id=student_id,
        selected_class=selected_class
    )


@main.route('/admin/attendance-analytics')
@login_required
def admin_attendance_analytics():

    if current_user.role != 'admin':
        return 'Access Denied', 403

    # Get filter values
    class_id = request.args.get('class_id')
    subject_id = request.args.get('subject_id')

    # Dropdown data
    classes = Class.query.order_by(
        Class.class_name,
        Class.section
    ).all()

    subjects = Subject.query.order_by(
        Subject.subject_name
    ).all()

    # Start attendance query
    query = Attendance.query

    # Class filter
    if class_id:
        query = query.filter(
            Attendance.class_id == int(class_id)
        )

    # Subject filter
    if subject_id:
        query = query.filter(
            Attendance.subject_id == int(subject_id)
        )

    attendance_records = query.all()

    # --------------------------------
    # Overall statistics
    # --------------------------------

    total_records = len(attendance_records)

    present_count = sum(
        1
        for record in attendance_records
        if record.status == 'Present'
    )

    absent_count = sum(
        1
        for record in attendance_records
        if record.status == 'Absent'
    )

    if total_records > 0:
        overall_percentage = (
            present_count / total_records
        ) * 100
    else:
        overall_percentage = 0


    # --------------------------------
    # Subject-wise analytics
    # --------------------------------

    subject_reports = {}

    for record in attendance_records:

        subject = Subject.query.get(
            record.subject_id
        )

        if not subject:
            continue

        if subject.id not in subject_reports:

            subject_reports[subject.id] = {
                'subject': subject,
                'total': 0,
                'present': 0,
                'absent': 0
            }

        subject_reports[
            subject.id
        ]['total'] += 1

        if record.status == 'Present':

            subject_reports[
                subject.id
            ]['present'] += 1

        elif record.status == 'Absent':

            subject_reports[
                subject.id
            ]['absent'] += 1


    # --------------------------------
    # Calculate percentages
    # --------------------------------

    for report in subject_reports.values():

        if report['total'] > 0:

            report['percentage'] = (
                report['present']
                / report['total']
            ) * 100

        else:

            report['percentage'] = 0


    # Convert dictionary to list
    subject_reports = list(
        subject_reports.values()
    )


    # --------------------------------
    # Chart data
    # --------------------------------

    chart_subject_names = [
        report['subject'].subject_name
        for report in subject_reports
    ]

    chart_subject_percentages = [
        round(report['percentage'], 2)
        for report in subject_reports
    ]

    chart_subject_present = [
        report['present']
        for report in subject_reports
    ]

    chart_subject_absent = [
        report['absent']
        for report in subject_reports
    ]


    return render_template(
        'admin/attendance_analytics.html',

        classes=classes,
        subjects=subjects,

        selected_class_id=class_id,
        selected_subject_id=subject_id,

        total_records=total_records,
        present_count=present_count,
        absent_count=absent_count,
        overall_percentage=overall_percentage,

        subject_reports=subject_reports,

        # Chart data
        chart_subject_names=chart_subject_names,
        chart_subject_percentages=chart_subject_percentages,
        chart_subject_present=chart_subject_present,
        chart_subject_absent=chart_subject_absent
    )