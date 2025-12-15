"""
Система учёта прохождения онлайн-курсов для персонала
Основной модуль приложения
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import json
from pathlib import Path
from reports import ReportGenerator

# Инициализация приложения
app = Flask(__name__)
CORS(app)

# Конфигурация базы данных
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "courses.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация БД
db = SQLAlchemy(app)

# ================== МОДЕЛИ ДАННЫХ ==================

class Employee(db.Model):
    """Модель для сотрудников"""
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    position = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)
    
    # Отношения
    registrations = db.relationship('Registration', backref='employee', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'phone': self.phone,
            'position': self.position,
            'created_at': self.created_at.isoformat(),
            'is_deleted': self.is_deleted
        }
    
    def __repr__(self):
        return f'<Employee {self.full_name}>'


class Course(db.Model):
    """Модель для курсов"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, unique=True)
    duration_hours = db.Column(db.Integer, nullable=False)
    certificate_type = db.Column(db.String(100), nullable=False)  # Диплом, Сертификат, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)
    
    # Отношения
    registrations = db.relationship('Registration', backref='course', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'duration_hours': self.duration_hours,
            'certificate_type': self.certificate_type,
            'created_at': self.created_at.isoformat(),
            'is_deleted': self.is_deleted
        }
    
    def __repr__(self):
        return f'<Course {self.title}>'


class Registration(db.Model):
    """Модель для регистрации сотрудников на курсы"""
    __tablename__ = 'registrations'
    
    STATUS_ENROLLED = 'enrolled'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    
    VALID_STATUSES = [STATUS_ENROLLED, STATUS_IN_PROGRESS, STATUS_COMPLETED]
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    status = db.Column(db.String(50), default=STATUS_ENROLLED, nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    progress_percent = db.Column(db.Integer, default=0)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)
    
    __table_args__ = (db.UniqueConstraint('employee_id', 'course_id', name='unique_registration'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.full_name if self.employee else None,
            'course_id': self.course_id,
            'course_title': self.course.title if self.course else None,
            'status': self.status,
            'registered_at': self.registered_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress_percent': self.progress_percent,
            'is_deleted': self.is_deleted
        }
    
    def __repr__(self):
        return f'<Registration {self.employee_id}-{self.course_id}>'


# ================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==================

VALID_POSITIONS = ['Аналитик', 'Разработчик', 'Тестировщик', 'Менеджер проекта', 
                   'Системный администратор', 'Дизайнер', 'Архитектор ПО']

def validate_phone(phone):
    """Валидация номера телефона"""
    phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    return phone.isdigit() and len(phone) >= 10

def validate_full_name(full_name):
    """Валидация ФИО"""
    if not full_name or len(full_name) < 3:
        return False
    return all(c.isalpha() or c.isspace() for c in full_name)

def validate_position(position):
    """Валидация должности"""
    return position in VALID_POSITIONS

def validate_course_duration(duration):
    """Валидация длительности курса"""
    try:
        hours = int(duration)
        return 1 <= hours <= 10000
    except (ValueError, TypeError):
        return False

def validate_certificate_type(cert_type):
    """Валидация типа документа"""
    valid_types = ['Диплом', 'Сертификат', 'Удостоверение', 'Свидетельство']
    return cert_type in valid_types

# ================== REST API ENDPOINTS ==================

# ===== Сотрудники =====

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """Получить всех сотрудников"""
    deleted = request.args.get('deleted', 'false').lower() == 'true'
    employees = Employee.query.filter_by(is_deleted=deleted).all()
    return jsonify([emp.to_dict() for emp in employees])


@app.route('/api/employees', methods=['POST'])
def create_employee():
    """Добавить нового сотрудника"""
    data = request.get_json()
    
    # Валидация данных
    if not data.get('full_name') or not validate_full_name(data['full_name']):
        return jsonify({'error': 'Некорректное ФИО'}), 400
    
    if not data.get('phone') or not validate_phone(data['phone']):
        return jsonify({'error': 'Некорректный номер телефона'}), 400
    
    if not data.get('position') or not validate_position(data['position']):
        return jsonify({'error': f'Должность должна быть одной из: {", ".join(VALID_POSITIONS)}'}), 400
    
    # Проверка уникальности
    existing = Employee.query.filter(
        (Employee.phone == data['phone']) & 
        (Employee.is_deleted == False)
    ).first()
    
    if existing:
        return jsonify({'error': 'Сотрудник с таким номером телефона уже существует'}), 400
    
    # Проверка на дубликаты по ФИО и должности
    duplicate = Employee.query.filter(
        (Employee.full_name == data['full_name']) & 
        (Employee.position == data['position']) &
        (Employee.is_deleted == False)
    ).first()
    
    if duplicate:
        return jsonify({'error': 'Сотрудник с таким ФИО и должностью уже существует'}), 400
    
    employee = Employee(
        full_name=data['full_name'],
        phone=data['phone'],
        position=data['position']
    )
    
    db.session.add(employee)
    db.session.commit()
    
    return jsonify(employee.to_dict()), 201


@app.route('/api/employees/<int:emp_id>', methods=['GET'])
def get_employee(emp_id):
    """Получить сотрудника по ID"""
    employee = Employee.query.get_or_404(emp_id)
    return jsonify(employee.to_dict())


@app.route('/api/employees/search', methods=['GET'])
def search_employees():
    """Поиск сотрудников по ФИО или номеру телефона"""
    query = request.args.get('q', '').strip()
    deleted = request.args.get('deleted', 'false').lower() == 'true'
    
    if not query:
        return jsonify({'error': 'Параметр поиска не может быть пустым'}), 400
    
    employees = Employee.query.filter(
        (Employee.is_deleted == deleted) &
        ((Employee.full_name.ilike(f'%{query}%')) | 
         (Employee.phone.contains(query)))
    ).all()
    
    return jsonify([emp.to_dict() for emp in employees])


@app.route('/api/employees/<int:emp_id>', methods=['DELETE'])
def delete_employee(emp_id):
    """Удалить сотрудника (мягкое удаление)"""
    employee = Employee.query.get_or_404(emp_id)
    employee.is_deleted = True
    employee.deleted_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Сотрудник удален'}), 200


# ===== Курсы =====

@app.route('/api/courses', methods=['GET'])
def get_courses():
    """Получить все курсы"""
    deleted = request.args.get('deleted', 'false').lower() == 'true'
    courses = Course.query.filter_by(is_deleted=deleted).all()
    return jsonify([course.to_dict() for course in courses])


@app.route('/api/courses', methods=['POST'])
def create_course():
    """Добавить новый курс"""
    data = request.get_json()
    
    # Валидация
    if not data.get('title') or len(data['title']) < 3:
        return jsonify({'error': 'Название курса должно быть длиной минимум 3 символа'}), 400
    
    if not validate_course_duration(data.get('duration_hours')):
        return jsonify({'error': 'Длительность должна быть от 1 до 10000 часов'}), 400
    
    if not validate_certificate_type(data.get('certificate_type')):
        return jsonify({'error': 'Выберите валидный тип документа'}), 400
    
    # Проверка уникальности названия
    existing = Course.query.filter(
        (Course.title == data['title']) &
        (Course.is_deleted == False)
    ).first()
    
    if existing:
        return jsonify({'error': 'Курс с таким названием уже существует'}), 400
    
    course = Course(
        title=data['title'],
        duration_hours=int(data['duration_hours']),
        certificate_type=data['certificate_type']
    )
    
    db.session.add(course)
    db.session.commit()
    
    return jsonify(course.to_dict()), 201


@app.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """Получить курс по ID"""
    course = Course.query.get_or_404(course_id)
    return jsonify(course.to_dict())


@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    """Удалить курс (мягкое удаление)"""
    course = Course.query.get_or_404(course_id)
    course.is_deleted = True
    course.deleted_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Курс удален'}), 200


# ===== Регистрации на курсы =====

@app.route('/api/registrations', methods=['GET'])
def get_registrations():
    """Получить все регистрации"""
    deleted = request.args.get('deleted', 'false').lower() == 'true'
    registrations = Registration.query.filter_by(is_deleted=deleted).all()
    return jsonify([reg.to_dict() for reg in registrations])


@app.route('/api/registrations', methods=['POST'])
def create_registration():
    """Зачислить сотрудника на курс"""
    data = request.get_json()
    
    employee_id = data.get('employee_id')
    course_id = data.get('course_id')
    
    if not employee_id or not course_id:
        return jsonify({'error': 'Необходимо указать сотрудника и курс'}), 400
    
    # Проверка существования
    employee = Employee.query.get_or_404(employee_id)
    course = Course.query.get_or_404(course_id)
    
    # Проверка дублирования
    existing = Registration.query.filter(
        (Registration.employee_id == employee_id) &
        (Registration.course_id == course_id) &
        (Registration.is_deleted == False)
    ).first()
    
    if existing:
        return jsonify({'error': 'Сотрудник уже зачислен на этот курс'}), 400
    
    registration = Registration(
        employee_id=employee_id,
        course_id=course_id,
        status=Registration.STATUS_ENROLLED
    )
    
    db.session.add(registration)
    db.session.commit()
    
    return jsonify(registration.to_dict()), 201


@app.route('/api/registrations/<int:reg_id>/status', methods=['PUT'])
def update_registration_status(reg_id):
    """Обновить статус прохождения курса"""
    registration = Registration.query.get_or_404(reg_id)
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in Registration.VALID_STATUSES:
        return jsonify({'error': f'Статус должен быть одним из: {", ".join(Registration.VALID_STATUSES)}'}), 400
    
    # Логика жизненного цикла
    if new_status == Registration.STATUS_IN_PROGRESS:
        if registration.status != Registration.STATUS_ENROLLED:
            return jsonify({'error': 'Можно начать курс только из статуса "Зачислен"'}), 400
        registration.started_at = datetime.utcnow()
    
    elif new_status == Registration.STATUS_COMPLETED:
        if registration.status != Registration.STATUS_IN_PROGRESS:
            return jsonify({'error': 'Можно завершить только курс, который начат'}), 400
        registration.completed_at = datetime.utcnow()
        registration.progress_percent = 100
    
    registration.status = new_status
    db.session.commit()
    
    return jsonify(registration.to_dict()), 200


@app.route('/api/registrations/<int:reg_id>/progress', methods=['PUT'])
def update_registration_progress(reg_id):
    """Обновить прогресс прохождения курса"""
    registration = Registration.query.get_or_404(reg_id)
    data = request.get_json()
    progress = data.get('progress_percent', 0)
    
    if not (0 <= progress <= 100):
        return jsonify({'error': 'Прогресс должен быть от 0 до 100'}), 400
    
    registration.progress_percent = progress
    if progress > 0 and registration.status == Registration.STATUS_ENROLLED:
        registration.status = Registration.STATUS_IN_PROGRESS
        registration.started_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(registration.to_dict()), 200


@app.route('/api/registrations/<int:reg_id>', methods=['DELETE'])
def delete_registration(reg_id):
    """Удалить регистрацию (мягкое удаление)"""
    registration = Registration.query.get_or_404(reg_id)
    registration.is_deleted = True
    registration.deleted_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Регистрация удалена'}), 200


# ===== Статистика и отчёты =====

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Получить статистику"""
    total_employees = Employee.query.filter_by(is_deleted=False).count()
    total_courses = Course.query.filter_by(is_deleted=False).count()
    total_registrations = Registration.query.filter_by(is_deleted=False).count()
    
    completed = Registration.query.filter(
        (Registration.status == Registration.STATUS_COMPLETED) &
        (Registration.is_deleted == False)
    ).count()
    
    in_progress = Registration.query.filter(
        (Registration.status == Registration.STATUS_IN_PROGRESS) &
        (Registration.is_deleted == False)
    ).count()
    
    by_status = {
        'enrolled': Registration.query.filter(
            (Registration.status == Registration.STATUS_ENROLLED) &
            (Registration.is_deleted == False)
        ).count(),
        'in_progress': in_progress,
        'completed': completed
    }
    
    # Популярные курсы
    popular_courses = db.session.query(
        Course.title,
        db.func.count(Registration.id).label('count')
    ).join(Registration).filter(
        Registration.is_deleted == False
    ).group_by(Course.id).order_by(db.func.count(Registration.id).desc()).limit(5).all()
    
    return jsonify({
        'total_employees': total_employees,
        'total_courses': total_courses,
        'total_registrations': total_registrations,
        'by_status': by_status,
        'popular_courses': [{'title': c[0], 'count': c[1]} for c in popular_courses]
    })


@app.route('/api/report/generate', methods=['GET'])
def generate_report():
    """Сгенерировать CSV отчёт с рекомендациями"""
    from reports import ReportGenerator
    
    generator = ReportGenerator()
    file_path = generator.generate_full_report()
    
    return send_file(file_path, as_attachment=True, download_name='course_report.csv')

@app.route('/api/report/view-html', methods=['GET'])
def view_html_report():
    """Просмотр HTML отчёта в браузере (2 листа A4)"""
    from flask import send_file
    generator = ReportGenerator()
    file_path = generator.generate_detailed_html_report()
    return send_file(file_path, mimetype='text/html')

@app.route('/api/report/download-html', methods=['GET'])
def download_html_report():
    """Скачивание HTML отчёта"""
    from flask import send_file
    generator = ReportGenerator()
    file_path = generator.generate_detailed_html_report()
    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"course_report_{datetime.now().strftime('%d_%m_%Y')}.html",
        mimetype='text/html'
    )


@app.route('/api/report/recommendations', methods=['GET'])
def get_recommendations():
    """Получить рекомендации по улучшению"""
    from reports import ReportGenerator
    
    generator = ReportGenerator()
    recommendations = generator.get_recommendations()
    
    return jsonify(recommendations)


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    """Главная страница"""
    return render_template('index.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5001)

