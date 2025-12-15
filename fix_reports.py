#!/usr/bin/env python3
"""
Авто‑починка reports.py и app.py для генерации отчётов без ошибок.

Что делает:
1) Полностью переписывает reports.py на простую и рабочую версию.
2) Убеждается, что в app.py есть корректный импорт ReportGenerator.
После запуска перезапусти приложение:  python app.py
"""

import io
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
APP_PY = BASE / "app.py"
REPORTS_PY = BASE / "reports.py"

REPORTS_CONTENT = r'''from datetime import datetime, timedelta
import csv
import os

from flask import current_app


class ReportGenerator:
    """
    Простой генератор отчётов.
    Без циклических импортов, с реальными данными из БД.
    """

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)

    def _get_models(self):
        """
        Локальный импорт моделей, чтобы не было циклического импорта на уровне модуля.
        Вызывается только внутри уже инициализированного приложения.
        """
        from app import Employee, Course, Registration
        return Employee, Course, Registration

    def _short_stats(self):
        """Краткая статистика для CSV."""
        Employee, Course, Registration = self._get_models()
        # generate_report вызывается из Flask‑ручки, контекст уже есть
        total_employees = Employee.query.filter_by(is_deleted=False).count()
        total_courses = Course.query.filter_by(is_deleted=False).count()
        total_regs = Registration.query.filter_by(is_deleted=False).count()
        return total_employees, total_courses, total_regs

    def _detailed_stats(self):
        """Расширенная статистика для HTML‑отчёта и рекомендаций."""
        Employee, Course, Registration = self._get_models()

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
        """Простой CSV‑отчёт (метрики)."""
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
        """
        Подробный HTML‑отчёт (2 листа A4 условно).
        Для простоты здесь формируется минимальный, но рабочий шаблон.
        Его можно доукрашивать отдельно.
        """
        stats = self._detailed_stats()
        filename = os.path.join(self.reports_dir, f"detailed_report_{self.timestamp}.html")

        completion_rate = (stats["completed"] / stats["total_regs"] * 100) if stats["total_regs"] else 0.0
        employee_engagement = (
            ((stats["total_employees"] - stats["employees_without_courses"]) / stats["total_employees"] * 100)
            if stats["total_employees"] else 0.0
        )

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Отчёт о прохождении курсов</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 40px; }}
h1 {{ color: #4b4bf5; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
th, td {{ border: 1px solid #ccc; padding: 6px 8px; font-size: 13px; }}
th {{ background: #eee; }}
.section {{ margin-top: 24px; }}
.badge {{ display:inline-block; padding:2px 6px; background:#4b4bf5; color:#fff; border-radius:8px; font-size:11px; }}
</style>
</head>
<body>
<h1>Отчёт о прохождении онлайн‑курсов</h1>
<p>Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>

<div class="section">
  <h2>Основные метрики</h2>
  <table>
    <tr><th>Показатель</th><th>Значение</th></tr>
    <tr><td>Сотрудников</td><td>{stats['total_employees']}</td></tr>
    <tr><td>Курсов</td><td>{stats['total_courses']}</td></tr>
    <tr><td>Регистраций</td><td>{stats['total_regs']}</td></tr>
    <tr><td>Процент завершения</td><td>{completion_rate:.1f}%</td></tr>
    <tr><td>Вовлечённость сотрудников</td><td>{employee_engagement:.1f}%</td></tr>
    <tr><td>Средний прогресс</td><td>{stats['avg_progress']}%</td></tr>
    <tr><td>Средняя длительность курса</td><td>{stats['avg_hours']} ч</td></tr>
  </table>
</div>

<div class="section">
  <h2>Распределение по статусам</h2>
  <table>
    <tr><th>Статус</th><th>Количество</th></tr>
    <tr><td>Зачислены</td><td>{stats['enrolled']}</td></tr>
    <tr><td>В процессе</td><td>{stats['in_progress']}</td></tr>
    <tr><td>Завершено</td><td>{stats['completed']}</td></tr>
  </table>
</div>

<div class="section">
  <h2>Популярность курсов</h2>
  <table>
    <tr><th>Курс</th><th>Регистраций</th><th>% от всех</th></tr>"""
        if stats["course_stats"]:
            total = sum(stats["course_stats"].values())
            for name, cnt in sorted(stats["course_stats"].items(), key=lambda x: x[1], reverse=True):
                pct = cnt / total * 100 if total else 0
                html += f"<tr><td>{name}</td><td>{cnt}</td><td>{pct:.1f}%</td></tr>"
        else:
            html += "<tr><td colspan='3'>Нет данных</td></tr>"
        html += f"""  </table>
</div>

<div class="section">
  <h2>Эвристики</h2>
  <ul>
"""

        # Простые эвристики
        if employee_engagement < 50:
            html += "<li>Низкая вовлечённость сотрудников — рекомендуется дополнительная мотивация.</li>"
        elif employee_engagement >= 80:
            html += "<li>Высокая вовлечённость — сильная культура обучения.</li>"

        if completion_rate < 40:
            html += "<li>Низкий процент завершения курсов — стоит пересмотреть программы.</li>"
        elif completion_rate > 70:
            html += "<li>Высокий процент завершения курсов — текущие программы эффективны.</li>"

        if stats["employees_without_courses"] > 0:
            html += f"<li>{stats['employees_without_courses']} сотрудников ещё не записаны ни на один курс.</li>"

        html += f"""
    <li>За последние 30 дней зарегистрировано {stats['recent_regs']} новых прохождений курсов.</li>
  </ul>
</div>

</body>
</html>"""

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        return filename

    def get_recommendations(self):
        """Краткие рекомендации для дашборда."""
        stats = self._detailed_stats()
        recs = []
        if stats["total_regs"] == 0:
            recs.append({
                "title": "Нет регистраций",
                "description": "Добавьте хотя бы одну регистрацию, чтобы получить аналитику."
            })
        else:
            recs.append({
                "title": f"Активных регистраций: {stats['total_regs']}",
                "description": "Система обучения активно используется."
            })
        return recs
'''

def patch_app_py():
    txt = APP_PY.read_text(encoding="utf-8")
    if "from reports import ReportGenerator" not in txt:
        # добавим импорт рядом с другими
        lines = txt.splitlines()
        insert_at = 0
        for i, line in enumerate(lines[:40]):
            if line.startswith("from") or line.startswith("import"):
                insert_at = i + 1
        lines.insert(insert_at, "from reports import ReportGenerator")
        APP_PY.write_text("\n".join(lines), encoding="utf-8")

def main():
    # 1. Перезаписываем reports.py
    REPORTS_PY.write_text(REPORTS_CONTENT, encoding="utf-8")
    print("✅ reports.py переписан на стабильную версию")

    # 2. Патчим app.py (импорт ReportGenerator)
    if APP_PY.exists():
        patch_app_py()
        print("✅ app.py: импорт ReportGenerator проверен/добавлен")
    else:
        print("⚠️ app.py не найден рядом со скриптом")

    print("\nТеперь перезапусти приложение:\n")
    print("    python app.py\n")

if __name__ == "__main__":
    main()
