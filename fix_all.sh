#!/bin/bash
echo "🔥 ФИКСИМ CORS + ПОРТЫ..."

# Остановить Flask
pkill -f flask 2>/dev/null

# Фикс app.js - ВСЕ 5000 → 5001
sed -i '' 's/localhost:5000/localhost:5001/g' static/app.js
echo "✅ app.js: localhost:5001"

# Фикс app.py - порт 5001
sed -i '' 's/port=[0-9]\{4\}/port=5001/g' app.py
echo "✅ app.py: port=5001"

# Проверить API_URL
grep "API_URL" static/app.js

# Запустить
echo "🚀 Запуск на http://localhost:5001..."
python app.py
