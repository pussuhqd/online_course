"""
Генератор отчётов о прохождении курсов.

Гарантии:
- Нет циклических импортов: reports.py НЕ импортирует app.py и модели на уровне модуля.
- Используется тот же Flask-SQLAlchemy, что привязан к текущему Flask app:
  current_app.extensions["sqlalchemy"].
- Учитывает реальную модель Registration:
  progress_percent, registered_at, status, is_deleted.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import csv
import os

from flask import current_app


def _get_sqla():
    """
    В Flask-SQLAlchemy 3.x app.extensions["sqlalchemy"] хранит extension (SQLAlchemy instance).
    В будущих версиях .db может быть удалён, поэтому берём сам extension как db.
    """
    app = current_app._get_current_object()
    ext = app.extensions.get("sqlalchemy")
    if ext is None:
        raise RuntimeError('Flask-SQLAlchemy не найден: current_app.extensions["sqlalchemy"] пуст')
    # совместимость: если вдруг ext.db существует — используем, иначе ext и есть db
    return getattr(ext, "db", ext)


def _get_registry(db):
    reg = getattr(getattr(db.Model, "registry", None), "_class_registry", None)
    if reg is not None:
        return reg
    reg = getattr(db.Model, "_decl_class_registry", None)
    if reg is not None:
        return reg
    raise RuntimeError("Не удалось получить registry моделей из db.Model")


def _get_models():
    db = _get_sqla()
    reg = _get_registry(db)

    Employee = reg.get("Employee")
    Course = reg.get("Course")
    Registration = reg.get("Registration")

    if not all([Employee, Course, Registration]):
        raise RuntimeError("Не найдены модели Employee/Course/Registration в registry")
    return Employee, Course, Registration


def _course_title(course) -> str:
    return getattr(course, "title", None) or getattr(course, "name", None) or f"Course #{getattr(course, 'id', '')}"


def _course_hours(course) -> float:
    for attr in ("duration_hours", "hours", "duration"):
        if hasattr(course, attr):
            try:
                return float(getattr(course, attr) or 0)
            except Exception:
                return 0.0
    return 0.0


class ReportGenerator:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)

    def _stats(self) -> dict:
        Employee, Course, Registration = _get_models()

        total_employees = Employee.query.filter_by(is_deleted=False).count()
        total_courses = Course.query.filter_by(is_deleted=False).count()
        total_regs = Registration.query.filter_by(is_deleted=False).count()

        enrolled = Registration.query.filter_by(status="enrolled", is_deleted=False).count()
        in_progress = Registration.query.filter_by(status="in_progress", is_deleted=False).count()
        completed = Registration.query.filter_by(status="completed", is_deleted=False).count()

        regs = Registration.query.filter_by(is_deleted=False).all()
        avg_progress = (sum(int(r.progress_percent or 0) for r in regs) / len(regs)) if regs else 0.0

        courses = Course.query.filter_by(is_deleted=False).all()
        avg_hours = (sum(_course_hours(c) for c in courses) / len(courses)) if courses else 0.0

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_regs = Registration.query.filter(
            Registration.registered_at >= thirty_days_ago,
            Registration.is_deleted == False,  # noqa: E712
        ).count()

        employees_with_courses = {r.employee_id for r in regs}
        all_employees = Employee.query.filter_by(is_deleted=False).all()
        employees_without_courses = len(all_employees) - len(employees_with_courses)

        course_stats = {}
        for c in courses:
            cnt = Registration.query.filter_by(course_id=c.id, is_deleted=False).count()
            if cnt > 0:
                course_stats[_course_title(c)] = cnt

        return {
            "total_employees": int(total_employees),
            "total_courses": int(total_courses),
            "total_regs": int(total_regs),
            "enrolled": int(enrolled),
            "in_progress": int(in_progress),
            "completed": int(completed),
            "avg_progress": round(avg_progress, 1),
            "avg_hours": round(avg_hours, 1),
            "recent_regs": int(recent_regs),
            "employees_without_courses": int(employees_without_courses),
            "course_stats": course_stats,
        }

    def generate_full_report(self) -> str:
        s = self._stats()
        filename = os.path.join(self.reports_dir, f"course_report_{self.timestamp}.csv")

        with open(filename, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["📊 ОТЧЁТ О ПРОХОЖДЕНИИ КУРСОВ"])
            w.writerow([f"Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}"])
            w.writerow([])
            w.writerow(["МЕТРИКИ"])
            w.writerow(["Сотрудников", s["total_employees"]])
            w.writerow(["Курсов", s["total_courses"]])
            w.writerow(["Регистраций", s["total_regs"]])
            w.writerow(["Зачислены", s["enrolled"]])
            w.writerow(["В процессе", s["in_progress"]])
            w.writerow(["Завершено", s["completed"]])
            w.writerow(["Средний прогресс, %", s["avg_progress"]])
            w.writerow(["Средняя длительность курса, ч", s["avg_hours"]])
            w.writerow(["Регистраций за 30 дней", s["recent_regs"]])
            w.writerow(["Сотрудников без курсов", s["employees_without_courses"]])

        return filename

    def generate_detailed_html_report(self) -> str:
        s = self._stats()
        filename = os.path.join(self.reports_dir, f"detailed_report_{self.timestamp}.html")

        completion_rate = (s["completed"] / s["total_regs"] * 100) if s["total_regs"] else 0.0
        engagement = (
            ((s["total_employees"] - s["employees_without_courses"]) / s["total_employees"] * 100)
            if s["total_employees"] else 0.0
        )

        if s["course_stats"]:
            total = sum(s["course_stats"].values()) or 1
            rows = "\n".join(
                f"<tr><td>{title}</td><td>{cnt}</td><td>{(cnt/total*100):.1f}%</td></tr>"
                for title, cnt in sorted(s["course_stats"].items(), key=lambda x: x[1], reverse=True)
            )
        else:
            rows = "<tr><td colspan='3'>Нет данных</td></tr>"

        html = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Отчёт о прохождении курсов</title>
<style>
body{{font-family:Arial,sans-serif;margin:24px;color:#111}}
table{{border-collapse:collapse;width:100%;margin:10px 0 16px}}
th,td{{border:1px solid #ddd;padding:6px 8px;font-size:13px}}
th{{background:#f3f4f6}}
.pagebreak{{page-break-before:always}}
</style>
</head>
<body>
<h1>Отчёт о прохождении онлайн‑курсов</h1>
<div style="color:#666;font-size:12px">Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}</div>

<h2>Лист 1 — Метрики</h2>
<table>
<tr><th>Показатель</th><th>Значение</th></tr>
<tr><td>Сотрудников</td><td>{s['total_employees']}</td></tr>
<tr><td>Курсов</td><td>{s['total_courses']}</td></tr>
<tr><td>Регистраций</td><td>{s['total_regs']}</td></tr>
<tr><td>Процент завершения</td><td>{completion_rate:.1f}%</td></tr>
<tr><td>Вовлечённость</td><td>{engagement:.1f}%</td></tr>
<tr><td>Средний прогресс</td><td>{s['avg_progress']}%</td></tr>
<tr><td>Средняя длительность курса</td><td>{s['avg_hours']} ч</td></tr>
</table>

<div class="pagebreak"></div>
<h2>Лист 2 — Популярность курсов</h2>
<table>
<tr><th>Курс</th><th>Регистраций</th><th>%</th></tr>
{rows}
</table>

</body>
</html>
"""

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        return filename

    def get_recommendations(self):
        s = self._stats()

        if s["total_regs"] == 0:
            return [{"title": "Нет регистраций", "description": "Добавьте хотя бы одну регистрацию для аналитики."}]

        completion_rate = (s["completed"] / s["total_regs"] * 100) if s["total_regs"] else 0.0
        engagement = (
            ((s["total_employees"] - s["employees_without_courses"]) / s["total_employees"] * 100)
            if s["total_employees"] else 0.0
        )

        recs = []
        if completion_rate < 40:
            recs.append({"title": "Низкий процент завершения", "description": "Пересмотрите длительность/сложность курсов и мотивацию."})
        if engagement < 50:
            recs.append({"title": "Низкая вовлечённость", "description": "Назначьте базовые обязательные курсы/план обучения."})
        if s["avg_progress"] < 50:
            recs.append({"title": "Низкий средний прогресс", "description": "Добавьте напоминания и контрольные точки."})

        if not recs:
            recs.append({"title": "Система стабильна", "description": "Показатели в норме, продолжайте мониторинг."})
        return recs
