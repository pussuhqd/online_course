#!/usr/bin/env python3
"""
Автоматическая генерация тестовых данных для демонстрации
"""

from app import app, db, Employee, Course, Registration
from datetime import datetime, timedelta

def seed_database():
    with app.app_context():
        # Удаляем старые данные
        db.session.query(Registration).delete()
        db.session.query(Employee).filter(Employee.is_deleted == False).delete()
        db.session.query(Course).filter(Course.is_deleted == False).delete()
        db.session.commit()
        
        print("�� База очищена")
        
        # СОТРУДНИКИ (7 человек)
        employees_data = [
            ("Полина Царева", "+79991234567", "Разработчик"),
            ("Иван Иванов", "+79997654321", "Тестировщик"),
            ("Мария Петрова", "+79995556677", "Аналитик"),
            ("Алексей Сидоров", "+79998887766", "Менеджер проекта"),
            ("Елена Козлова", "+79993334455", "Дизайнер"),
            ("Дмитрий Смирнов", "+79996665544", "Системный администратор"),
            ("Ольга Васильева", "+79997776655", "Архитектор ПО")
        ]
        
        employees = []
        for full_name, phone, position in employees_data:
            emp = Employee(full_name=full_name, phone=phone, position=position)
            db.session.add(emp)
            employees.append(emp)
        
        db.session.commit()
        print(f"✅ Добавлено {len(employees)} сотрудников")
        
        # КУРСЫ (6 курсов)
        courses_data = [
            ("Python для начинающих", 40, "Сертификат"),
            ("JavaScript Advanced", 60, "Диплом"),
            ("SQL и базы данных", 24, "Удостоверение"),
            ("Git и GitHub", 8, "Сертификат"),
            ("Docker для разработчиков", 16, "Сертификат"),
            ("React.js Fundamentals", 48, "Диплом")
        ]
        
        courses = []
        for title, duration, cert_type in courses_data:
            course = Course(title=title, duration_hours=duration, certificate_type=cert_type)
            db.session.add(course)
            courses.append(course)
        
        db.session.commit()
        print(f"✅ Добавлено {len(courses)} курсов")
        
        # РЕГИСТРАЦИИ (10 записей с разными статусами)
        registrations_data = [
            (employees[0], courses[0], "completed", 100),  # Полина - Python - завершено
            (employees[1], courses[0], "in_progress", 75), # Иван - Python - в процессе
            (employees[2], courses[1], "enrolled", 0),     # Мария - JS - зачислена
            (employees[3], courses[2], "completed", 100),  # Алексей - SQL - завершено
            (employees[0], courses[1], "in_progress", 45), # Полина - JS - в процессе
            (employees[4], courses[3], "enrolled", 0),     # Елена - Git - зачислена
            (employees[5], courses[4], "in_progress", 60), # Дмитрий - Docker - в процессе
            (employees[6], courses[5], "completed", 100),  # Ольга - React - завершено
            (employees[1], courses[2], "in_progress", 30), # Иван - SQL - в процессе
            (employees[2], courses[3], "enrolled", 0)      # Мария - Git - зачислена
        ]
        
        for emp, course, status, progress in registrations_data:
            reg = Registration(
                employee_id=emp.id,
                course_id=course.id,
                status=status,
                progress_percent=progress,
                registered_at=datetime.now() - timedelta(days=30)
            )
            if status == "in_progress":
                reg.started_at = datetime.now() - timedelta(days=20)
            elif status == "completed":
                reg.completed_at = datetime.now() - timedelta(days=10)
            
            db.session.add(reg)
        
        db.session.commit()
        print(f"✅ Добавлено {len(registrations_data)} регистраций")
        print("🎉 Тестовые данные готовы! Дашборд покажет статистику.")
        print("📱 Откройте: http://localhost:5001")

if __name__ == "__main__":
    seed_database()
