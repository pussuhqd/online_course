"""
Модульные тесты для системы учёта онлайн-курсов
"""

import pytest
import os
import tempfile
import json
from datetime import datetime
from app import app, db, Employee, Course, Registration


@pytest.fixture
def client():
    """Создать тестовый клиент Flask"""
    db_fd, db_path = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

    os.close(db_fd)
    os.unlink(db_path)


# ==================== ТЕСТЫ СОТРУДНИКОВ ====================

def test_create_employee(client):
    """Тест создания сотрудника"""
    response = client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['full_name'] == 'Иван Иванов'
    assert data['position'] == 'Разработчик'


def test_create_employee_invalid_phone(client):
    """Тест создания сотрудника с некорректным номером телефона"""
    response = client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '123',  # Слишком короткий
        'position': 'Разработчик'
    })
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_create_employee_invalid_name(client):
    """Тест создания сотрудника с некорректным ФИО"""
    response = client.post('/api/employees', json={
        'full_name': 'ИВ',  # Слишком короткое
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    
    assert response.status_code == 400


def test_create_employee_invalid_position(client):
    """Тест создания сотрудника с несуществующей должностью"""
    response = client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Супергерой'  # Несуществующая должность
    })
    
    assert response.status_code == 400


def test_create_duplicate_employee(client):
    """Тест создания дублирующегося сотрудника"""
    # Создаём первого сотрудника
    client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    
    # Пытаемся создать дубликат с тем же номером телефона
    response = client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_get_employees(client):
    """Тест получения списка сотрудников"""
    # Создаём сотрудников
    client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    
    client.post('/api/employees', json={
        'full_name': 'Петр Петров',
        'phone': '+79997654321',
        'position': 'Тестировщик'
    })
    
    response = client.get('/api/employees?deleted=false')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2


def test_search_employee_by_name(client):
    """Тест поиска сотрудника по ФИО"""
    client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    
    response = client.get('/api/employees/search?q=Иван')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['full_name'] == 'Иван Иванов'


def test_search_employee_by_phone(client):
    """Тест поиска сотрудника по номеру телефона"""
    client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    
    response = client.get('/api/employees/search?q=79991234567')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1


def test_delete_employee(client):
    """Тест удаления сотрудника"""
    # Создаём сотрудника
    create_response = client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    emp_id = json.loads(create_response.data)['id']
    
    # Удаляем сотрудника
    delete_response = client.delete(f'/api/employees/{emp_id}')
    assert delete_response.status_code == 200
    
    # Проверяем, что сотрудник удалён
    get_response = client.get('/api/employees?deleted=false')
    data = json.loads(get_response.data)
    assert len(data) == 0


# ==================== ТЕСТЫ КУРСОВ ====================

def test_create_course(client):
    """Тест создания курса"""
    response = client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': 40,
        'certificate_type': 'Сертификат'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['title'] == 'Python для начинающих'
    assert data['duration_hours'] == 40


def test_create_course_short_title(client):
    """Тест создания курса с коротким названием"""
    response = client.post('/api/courses', json={
        'title': 'П',  # Слишком короткое
        'duration_hours': 40,
        'certificate_type': 'Сертификат'
    })
    
    assert response.status_code == 400


def test_create_course_invalid_duration(client):
    """Тест создания курса с некорректной длительностью"""
    response = client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': -5,  # Отрицательное значение
        'certificate_type': 'Сертификат'
    })
    
    assert response.status_code == 400


def test_create_course_invalid_certificate(client):
    """Тест создания курса с несуществующим типом документа"""
    response = client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': 40,
        'certificate_type': 'Медаль'  # Несуществующий тип
    })
    
    assert response.status_code == 400


def test_create_duplicate_course(client):
    """Тест создания дублирующегося курса"""
    # Создаём первый курс
    client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': 40,
        'certificate_type': 'Сертификат'
    })
    
    # Пытаемся создать дубликат
    response = client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': 40,
        'certificate_type': 'Сертификат'
    })
    
    assert response.status_code == 400


def test_get_courses(client):
    """Тест получения списка курсов"""
    client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': 40,
        'certificate_type': 'Сертификат'
    })
    
    response = client.get('/api/courses?deleted=false')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1


def test_delete_course(client):
    """Тест удаления курса"""
    # Создаём курс
    create_response = client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': 40,
        'certificate_type': 'Сертификат'
    })
    course_id = json.loads(create_response.data)['id']
    
    # Удаляем курс
    delete_response = client.delete(f'/api/courses/{course_id}')
    assert delete_response.status_code == 200
    
    # Проверяем, что курс удалён
    get_response = client.get('/api/courses?deleted=false')
    data = json.loads(get_response.data)
    assert len(data) == 0


# ==================== ТЕСТЫ РЕГИСТРАЦИЙ ====================

def test_create_registration(client):
    """Тест создания регистрации"""
    # Создаём сотрудника и курс
    emp_resp = client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    emp_id = json.loads(emp_resp.data)['id']
    
    course_resp = client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': 40,
        'certificate_type': 'Сертификат'
    })
    course_id = json.loads(course_resp.data)['id']
    
    # Создаём регистрацию
    response = client.post('/api/registrations', json={
        'employee_id': emp_id,
        'course_id': course_id
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['status'] == 'enrolled'
    assert data['progress_percent'] == 0


def test_create_duplicate_registration(client):
    """Тест создания дублирующейся регистрации"""
    # Создаём сотрудника и курс
    emp_resp = client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    emp_id = json.loads(emp_resp.data)['id']
    
    course_resp = client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': 40,
        'certificate_type': 'Сертификат'
    })
    course_id = json.loads(course_resp.data)['id']
    
    # Создаём первую регистрацию
    client.post('/api/registrations', json={
        'employee_id': emp_id,
        'course_id': course_id
    })
    
    # Пытаемся создать дубликат
    response = client.post('/api/registrations', json={
        'employee_id': emp_id,
        'course_id': course_id
    })
    
    assert response.status_code == 400


def test_registration_lifecycle(client):
    """Тест жизненного цикла регистрации"""
    # Создаём сотрудника и курс
    emp_resp = client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    emp_id = json.loads(emp_resp.data)['id']
    
    course_resp = client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': 40,
        'certificate_type': 'Сертификат'
    })
    course_id = json.loads(course_resp.data)['id']
    
    # Создаём регистрацию (статус: enrolled)
    reg_resp = client.post('/api/registrations', json={
        'employee_id': emp_id,
        'course_id': course_id
    })
    reg_id = json.loads(reg_resp.data)['id']
    
    # Переводим в in_progress
    in_progress_resp = client.put(f'/api/registrations/{reg_id}/status', json={
        'status': 'in_progress'
    })
    assert in_progress_resp.status_code == 200
    
    # Переводим в completed
    completed_resp = client.put(f'/api/registrations/{reg_id}/status', json={
        'status': 'completed'
    })
    assert completed_resp.status_code == 200
    completed_data = json.loads(completed_resp.data)
    assert completed_data['progress_percent'] == 100


def test_registration_invalid_transition(client):
    """Тест недопустимого перехода статуса"""
    # Создаём сотрудника и курс
    emp_resp = client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    emp_id = json.loads(emp_resp.data)['id']
    
    course_resp = client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': 40,
        'certificate_type': 'Сертификат'
    })
    course_id = json.loads(course_resp.data)['id']
    
    # Создаём регистрацию
    reg_resp = client.post('/api/registrations', json={
        'employee_id': emp_id,
        'course_id': course_id
    })
    reg_id = json.loads(reg_resp.data)['id']
    
    # Пытаемся перейти сразу в completed (должно быть ошибкой)
    response = client.put(f'/api/registrations/{reg_id}/status', json={
        'status': 'completed'
    })
    
    assert response.status_code == 400


def test_update_progress(client):
    """Тест обновления прогресса"""
    # Создаём сотрудника и курс
    emp_resp = client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    emp_id = json.loads(emp_resp.data)['id']
    
    course_resp = client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': 40,
        'certificate_type': 'Сертификат'
    })
    course_id = json.loads(course_resp.data)['id']
    
    # Создаём регистрацию
    reg_resp = client.post('/api/registrations', json={
        'employee_id': emp_id,
        'course_id': course_id
    })
    reg_id = json.loads(reg_resp.data)['id']
    
    # Обновляем прогресс
    response = client.put(f'/api/registrations/{reg_id}/progress', json={
        'progress_percent': 50
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['progress_percent'] == 50


def test_get_registrations(client):
    """Тест получения списка регистраций"""
    # Создаём сотрудника и курс
    emp_resp = client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    emp_id = json.loads(emp_resp.data)['id']
    
    course_resp = client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': 40,
        'certificate_type': 'Сертификат'
    })
    course_id = json.loads(course_resp.data)['id']
    
    # Создаём регистрацию
    client.post('/api/registrations', json={
        'employee_id': emp_id,
        'course_id': course_id
    })
    
    response = client.get('/api/registrations?deleted=false')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1


def test_delete_registration(client):
    """Тест удаления регистрации"""
    # Создаём сотрудника и курс
    emp_resp = client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    emp_id = json.loads(emp_resp.data)['id']
    
    course_resp = client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': 40,
        'certificate_type': 'Сертификат'
    })
    course_id = json.loads(course_resp.data)['id']
    
    # Создаём регистрацию
    reg_resp = client.post('/api/registrations', json={
        'employee_id': emp_id,
        'course_id': course_id
    })
    reg_id = json.loads(reg_resp.data)['id']
    
    # Удаляем регистрацию
    delete_response = client.delete(f'/api/registrations/{reg_id}')
    assert delete_response.status_code == 200
    
    # Проверяем, что регистрация удалена
    get_response = client.get('/api/registrations?deleted=false')
    data = json.loads(get_response.data)
    assert len(data) == 0


# ==================== ТЕСТЫ СТАТИСТИКИ ====================

def test_get_statistics(client):
    """Тест получения статистики"""
    response = client.get('/api/statistics')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_employees' in data
    assert 'total_courses' in data
    assert 'total_registrations' in data
    assert 'by_status' in data


def test_statistics_with_data(client):
    """Тест статистики с данными"""
    # Создаём данные
    emp_resp = client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    emp_id = json.loads(emp_resp.data)['id']
    
    course_resp = client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': 40,
        'certificate_type': 'Сертификат'
    })
    course_id = json.loads(course_resp.data)['id']
    
    reg_resp = client.post('/api/registrations', json={
        'employee_id': emp_id,
        'course_id': course_id
    })
    
    # Получаем статистику
    response = client.get('/api/statistics')
    data = json.loads(response.data)
    
    assert data['total_employees'] == 1
    assert data['total_courses'] == 1
    assert data['total_registrations'] == 1
    assert data['by_status']['enrolled'] == 1


# ==================== ИНТЕГРАЦИОННЫЕ ТЕСТЫ ====================

def test_full_workflow(client):
    """Полный интеграционный тест"""
    # 1. Создаём сотрудников
    emp1_resp = client.post('/api/employees', json={
        'full_name': 'Иван Иванов',
        'phone': '+79991234567',
        'position': 'Разработчик'
    })
    emp1_id = json.loads(emp1_resp.data)['id']
    
    emp2_resp = client.post('/api/employees', json={
        'full_name': 'Петр Петров',
        'phone': '+79997654321',
        'position': 'Тестировщик'
    })
    emp2_id = json.loads(emp2_resp.data)['id']
    
    # 2. Создаём курсы
    course1_resp = client.post('/api/courses', json={
        'title': 'Python для начинающих',
        'duration_hours': 40,
        'certificate_type': 'Сертификат'
    })
    course1_id = json.loads(course1_resp.data)['id']
    
    course2_resp = client.post('/api/courses', json={
        'title': 'JavaScript Advanced',
        'duration_hours': 60,
        'certificate_type': 'Диплом'
    })
    course2_id = json.loads(course2_resp.data)['id']
    
    # 3. Зачисляем на курсы
    reg1_resp = client.post('/api/registrations', json={
        'employee_id': emp1_id,
        'course_id': course1_id
    })
    reg1_id = json.loads(reg1_resp.data)['id']
    
    reg2_resp = client.post('/api/registrations', json={
        'employee_id': emp2_id,
        'course_id': course1_id
    })
    reg2_id = json.loads(reg2_resp.data)['id']
    
    # 4. Обновляем статусы
    client.put(f'/api/registrations/{reg1_id}/status', json={
        'status': 'in_progress'
    })
    
    client.put(f'/api/registrations/{reg1_id}/progress', json={
        'progress_percent': 75
    })
    
    client.put(f'/api/registrations/{reg1_id}/status', json={
        'status': 'completed'
    })
    
    # 5. Проверяем статистику
    stats_resp = client.get('/api/statistics')
    stats = json.loads(stats_resp.data)
    
    assert stats['total_employees'] == 2
    assert stats['total_courses'] == 2
    assert stats['total_registrations'] == 2
    assert stats['by_status']['completed'] == 1
    assert stats['by_status']['enrolled'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
