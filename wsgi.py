"""
Инициализация приложения Flask
Этот файл можно использовать для запуска с через wsgi сервер
"""

import sys
import os

# Добавляем текущую директорию в path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db

if __name__ == '__main__':
    # Убедитесь, что база данных инициализирована
    with app.app_context():
        db.create_all()
    
    # Запуск приложения
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )
