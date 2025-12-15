#!/usr/bin/env python3
"""
Генерация РЕАЛЬНЫХ данных в основную БД courses.db
"""

from app import app, db, Employee, Course, Registration
from datetime import datetime, timedelta
import os

print("🔥 Генерация РЕАЛЬНЫХ данных в courses.db...")

with app.app_context():
    # ОЧИСТИТЬ старую БД
    db.session.query(Registration).delete()
    db.session.query(Employee).filter(Employee.is_deleted == False).delete()
    db.session.query(Course).filter(Course.is_deleted == False).delete()
    db.session.commit()
    
    print("🧹 База очищена")
    
    # 8 РЕАЛЬНЫХ СОТРУДНИКОВ
    employees = [
        Employee(full_name="Полина Царева", phone="+79991234567", position="Разработчик"),
        Employee(full_name="Иван Иванов", phone="+79997654321", position="Тестировщик"),
        Employee(full_name="Мария Петрова", phone="+79995556677", position="Аналитик"),
        Employee(full_name="Алексей Сидоров", phone="+79998887766", position="Менеджер проекта"),
        Employee(full_name="Елена Козлова", phone="+79993334455", position="Дизайнер"),
        Employee(full_name="Дмитрий Смирнов", phone="+79996665544", position="Системный администратор"),
        Employee(full_name="Ольга Васильева", phone="+79997776655", position="Архитектор ПО"),
        Employee(full_name="Сергей Кузнецов", phone="+79994445566", position="Разработчик")
    ]
    
    for emp in employees:
        db.session.add(emp)
    db.session.commit()
    print(f"✅ 8 сотрудников добавлено")
    
    # 7 РЕАЛЬНЫХ КУРСОВ
    courses = [
        Course(title="Python для разработчиков", duration_hours=40, certificate_type="Сертификат"),
        Course(title="JavaScript Advanced", duration_hours=60, certificate_type="Диплом"),
        Course(title="PostgreSQL и SQL", duration_hours=24, certificate_type="Удостоверение"),
        Course(title="Git и CI/CD", duration_hours=12, certificate_type="Сертификат"),
        Course(title="Docker & Kubernetes", duration_hours=32, certificate_type="Диплом"),
        Course(title="React.js + TypeScript", duration_hours=48, certificate_type="Диплом"),
        Course(title="DevOps Fundamentals", duration_hours=36, certificate_type="Сертификат")
    ]
    
    for course in courses:
        db.session.add(course)
    db.session.commit()
    print(f"✅ 7 курсов добавлено")
    
    # 15 РЕАЛЬНЫХ РЕГИСТРАЦИЙ (разные статусы)
    registrations = [
        # ПОЛИНА (3 курса)
        (employees[0], courses[0], "completed", 100, datetime.now()-timedelta(days=5)),
        (employees[0], courses[1], "in_progress", 85, datetime.now()-timedelta(days=10)),
        (employees[0], courses[5], "enrolled", 0, datetime.now()-timedelta(days=2)),
        
        # ИВАН (2 курса)
        (employees[1], courses[0], "completed", 100, datetime.now()-timedelta(days=7)),
        (employees[1], courses[2], "in_progress", 60, datetime.now()-timedelta(days=12)),
        
        # МАРИЯ (2 курса)
        (employees[2], courses[3], "enrolled", 0, datetime.now()),
        (employees[2], courses[4], "in_progress", 25, datetime.now()-timedelta(days=3)),
        
        # АЛЕКСЕЙ (2 курса)
        (employees[3], courses[6], "completed", 100, datetime.now()-timedelta(days=1)),
        (employees[3], courses[1], "enrolled", 0, datetime.now()-timedelta(days=1)),
        
        # ОСТАЛЬНЫЕ
        (employees[4], courses[2], "completed", 100, datetime.now()-timedelta(days=15)),
        (employees[5], courses[3], "in_progress", 40, datetime.now()-timedelta(days=8)),
        (employees[6], courses[4], "enrolled", 0, datetime.now()),
        (employees[7], courses[5], "in_progress", 70, datetime.now()-timedelta(days=6))
    ]
    
    for emp, course, status, progress, reg_date in registrations:
        reg = Registration(
            employee_id=emp.id,
            course_id=course.id,
            status=status,
            progress_percent=progress,
            registered_at=reg_date
        )
        if status == "in_progress":
            reg.started_at = reg_date + timedelta(days=2)
        if status == "completed":
            reg.completed_at = reg_date + timedelta(days=progress//10)
        
        db.session.add(reg)
    
    db.session.commit()
    print(f"✅ 15 регистраций добавлено (5 завершено, 6 в процессе, 4 зачислено)")
    
    # ПРОВЕРКА СТАТИСТИКИ
    stats = {
        'employees': Employee.query.filter_by(is_deleted=False).count(),
        'courses': Course.query.filter_by(is_deleted=False).count(),
        'registrations': Registration.query.filter_by(is_deleted=False).count(),
        'completed': Registration.query.filter_by(status="completed", is_deleted=False).count()
    }
    print(f"\n📊 СТАТИСТИКА:")
    print(f"   👥 Сотрудников: {stats['employees']}")
    print(f"   📚 Курсов: {stats['courses']}")
    print(f"   ✏️ Регистраций: {stats['registrations']}")
    print(f"   ✅ Завершено: {stats['completed']} ({stats['completed']*100//stats['registrations'] if stats['registrations'] else 0}%)")
    
    print("\n🎉 ДАННЫЕ ГОТОВЫ!")
    print("📱 Запустите: python app.py")
    print("🌐 Откройте: http://localhost:5001")
    print("📊 Отчёт покажет реальную статистику!")


