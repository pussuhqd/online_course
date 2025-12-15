#!/usr/bin/env bash
set -euo pipefail

echo "==> Переходим в папку проекта (где app.py)"
if [[ ! -f "app.py" ]]; then
  echo "ОШИБКА: app.py не найден. Запусти скрипт из папки exported-assets."
  exit 1
fi

echo "==> 1) Переписываем reports.py (без импортов app/db/моделей)"
cat > reports.py << 'PY'
from datetime import datetime, timedelta
import csv
import os

from flask import current_app


def _get_sqla_ext():
    """
    Достаём Flask-SQLAlchemy extension из текущего Flask app.
    Это гарантирует, что используется ТОТ ЖЕ db, который реально привязан к app.
    """
    app = current_app._get_current_object()
    ext = app.extensions.get("sqlalchemy")
    if not ext:
        raise RuntimeError("Flask-SQLAlchemy extension not found in current_app.extensions['sqlalchemy']")
    return ext


def _get_db():
    # В Flask-SQLAlchemy 3.x db лежит в ext.db
    ext = _get_sqla_ext()
    db = getattr(ext, "db", None)
    if db is None:
        raise RuntimeError("Cannot access db from Flask-SQLAlchemy extension (expected ext.db)")
    return db


def _get_model(db, name: str):
    """
    Ищем модель в registry. Это работает без импорта app.py и без циклов.
    """
    registry = getattr(db.Model, "registry", None)
    if registry is None or not hasattr(registry, "_class_registry"):
        raise RuntimeError("db.Model.registry._class_registry not available (unexpected Flask-SQLAlchemy version)")
    model = registry._class_registry.get(name)
    if model is None:
        raise RuntimeError(f"Model '{name}' not found in SQLAlchemy registry")
    return model


class ReportGenerator:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)

    def _models(self):
        db = _get_db()
        Employee = _get_model(db, "Employee")
        Course = _get_model(db, "Course")
        Registration = _get_model(db, "Registration")
        return Employee, Course, Registration

    def _short_stats(self):
        Employee, Course, Registration = self._models()
        total_employees = Employee.query.filter_by(is_deleted=False).count()
        total_courses = Course.query.filter_by(is_deleted=False).count()
        total_regs = Registration.query.filter_by(is_deleted=False).count()
        return total_employees, total_courses, total_regs

    def _detailed_stats(self):
        Employee, Course, Registration = self._models()

        total_employees = Employee.query.filter_by(is_deleted=False).count()
        total_courses = Course.query.filter_by(is_deleted=False).count()
        total_regs = Registration.query.filter_by(is_deleted=False).count()

        enrolled = Registration.query.filter_by(status="enrolled", is_deleted=False).count()
        in_progress = Registration.query.filter_by(status="in_progress", is_deleted=False).count()
        completed = Registration.query.filter_by(status="completed", is_deleted=False).count()

        regs = Registration.query.filter_by(is_deleted=False).all()
        avg_progress = (sum(r.progress for r in regs) / len(regs)) if regs else 0.0

        courses = Course.query.filter_by(is_deleted=False).all()
        course_stats = {}
        for c in courses:
            cnt = Registration.query.filter_by(course_id=c.id, is_deleted=False).count()
            if cnt > 0:
                course_stats[c.name] = cnt

        avg_hours = (sum(c.duration_hours for c in courses) / len(courses)) if courses else 0.0

        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_regs = Registration.query.filter(
            Registration.registered_date >= thirty_days_ago,
            Registration.is_deleted == False  # noqa: E712
        ).count()

        employees_with_courses = {r.employee_id for r in regs}
        all_employees = Employee.query.filter_by(is_deleted=False).all()
        employees_without_courses = len(all_employees) - len(employees_with_courses)

        return {
            "total_employees": total_employees,
            "total_courses": total_courses,
            "total_regs": total_regs,
            "enrolled": enrolled,
            "in_progress": in_progress,
            "completed": completed,
            "avg_progress": round(avg_progress, 1),
            "course_stats": course_stats,
            "avg_hours": round(avg_hours, 1),
            "recent_regs": recent_regs,
            "employees_without_courses": employees_without_courses,
        }

    def generate_full_report(self):
        total_employees, total_courses, total_regs = self._short_stats()
        filename = os.path.join(self.reports_dir, f"course_report_{self.timestamp}.csv")

        with open(filename, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["📊 ОТЧЁТ О ПРОХОЖДЕНИИ КУРСОВ"])
            w.writerow([f"Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}"])
            w.writerow([])
            w.writerow(["МЕТРИКИ"])
            w.writerow(["Сотрудников", total_employees])
            w.writerow(["Курсов", total_courses])
            w.writerow(["Регистраций", total_regs])

        return filename

    def generate_detailed_html_report(self):
        stats = self._detailed_stats()
        filename = os.path.join(self.reports_dir, f"detailed_report_{self.timestamp}.html")

        completion_rate = (stats["completed"] / stats["total_regs"] * 100) if stats["total_regs"] else 0.0
        employee_engagement = (
            ((stats["total_employees"] - stats["employees_without_courses"]) / stats["total_employees"] * 100)
            if stats["total_employees"] else 0.0
        )

        # Минимальный HTML (рабочий). Можно расширять, но главное — стабильность.
        html = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Отчёт о прохождении курсов</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 28px; }}
h1 {{ margin: 0 0 6px; }}
.small {{ color: #666; font-size: 12px; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0 18px; }}
th, td {{ border: 1px solid #ccc; padding: 6px 8px; font-size: 13px; }}
th {{ background: #f2f2f2; }}
.pagebreak {{ page-break-before: always; }}
</style>
</head>
<body>
<h1>Отчёт о прохождении онлайн‑курсов</h1>
<div class="small">Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}</div>

<h2>Лист 1 — Метрики</h2>
<table>
<tr><th>Показатель</th><th>Значение</th></tr>
<tr><td>Сотрудников</td><td>{stats['total_employees']}</td></tr>
<tr><td>Курсов</td><td>{stats['total_courses']}</td></tr>
<tr><td>Регистраций</td><td>{stats['total_regs']}</td></tr>
<tr><td>Завершено</td><td>{stats['completed']}</td></tr>
<tr><td>Процент завершения</td><td>{completion_rate:.1f}%</td></tr>
<tr><td>Вовлечённость</td><td>{employee_engagement:.1f}%</td></tr>
<tr><td>Средний прогресс</td><td>{stats['avg_progress']}%</td></tr>
<tr><td>Средняя длительность курса</td><td>{stats['avg_hours']} ч</td></tr>
</table>

<table>
<tr><th>Статус</th><th>Количество</th></tr>
<tr><td>Зачислены</td><td>{stats['enrolled']}</td></tr>
<tr><td>В процессе</td><td>{stats['in_progress']}</td></tr>
<tr><td>Завершено</td><td>{stats['completed']}</td></tr>
</table>

<div class="pagebreak"></div>
<h2>Лист 2 — Курсы и эвристики</h2>

<h3>Популярность курсов</h3>
<table>
<tr><th>Курс</th><th>Регистраций</th><th>% от всех (по курсам)</th></tr>
"""
        if stats["course_stats"]:
            total = sum(stats["course_stats"].values())
            for name, cnt in sorted(stats["course_stats"].items(), key=lambda x: x[1], reverse=True):
                pct = (cnt / total * 100) if total else 0
                html += f"<tr><td>{name}</td><td>{cnt}</td><td>{pct:.1f}%</td></tr>"
        else:
            html += "<tr><td colspan='3'>Нет данных</td></tr>"

        html += f"""
</table>

<h3>Эвристики</h3>
<ul>
<li>За 30 дней: {stats['recent_regs']} новых регистраций.</li>
<li>Сотрудников без курсов: {stats['employees_without_courses']}.</li>
<li>Если завершение ниже 40% — стоит пересмотреть нагрузку и мотивацию (текущее: {completion_rate:.1f}%).</li>
<li>Если вовлечённость ниже 50% — стоит назначить обязательные курсы (текущее: {employee_engagement:.1f}%).</li>
</ul>

</body></html>
"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        return filename

    def get_recommendations(self):
        stats = self._detailed_stats()
        recs = []
        if stats["total_regs"] == 0:
            recs.append({"title": "Нет регистраций", "description": "Добавьте хотя бы одну регистрацию, чтобы получить аналитику."})
        else:
            recs.append({"title": f"Активных регистраций: {stats['total_regs']}", "description": "Система обучения активно используется."})
        return recs
PY

echo "==> reports.py обновлён ✅"

echo "==> 2) Проверяем, что app.py импортирует ReportGenerator"
# Если нет импорта — добавим после первых импортов
python - << 'PY'
from pathlib import Path
p = Path("app.py")
txt = p.read_text(encoding="utf-8", errors="ignore").splitlines()

need = "from reports import ReportGenerator"
if any(line.strip() == need for line in txt):
    print("app.py: импорт уже есть ✅")
else:
    # вставим после последнего import в верхней части файла
    insert_at = 0
    for i, line in enumerate(txt[:80]):
        if line.startswith("import ") or line.startswith("from "):
            insert_at = i + 1
    txt.insert(insert_at, need)
    p.write_text("\n".join(txt), encoding="utf-8")
    print("app.py: импорт добавлен ✅")
PY

echo ""
echo "ГОТОВО."
echo "Теперь перезапусти сервер:"
echo "  pkill -f flask 2>/dev/null || true"
echo "  python app.py"
echo ""
