# 🚀 DEPLOYMENT - Развёртывание на сервер

## 📋 Требования для production

- Python 3.8+
- pip / virtualenv
- gunicorn или другой WSGI сервер
- nginx или Apache (reverse proxy)
- SSL сертификат (Let's Encrypt)
- PostgreSQL (опционально, вместо SQLite)

## 🔧 Шаг 1: Подготовка сервера

### Обновить систему (Ubuntu/Debian)
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx
```

### Для macOS
```bash
brew update
brew install python3 nginx
```

## 📦 Шаг 2: Установка приложения

### Загрузить файлы проекта
```bash
cd /var/www
sudo git clone https://your-repo/course-management.git
# или скопировать файлы через SFTP/SCP
```

### Создать виртуальное окружение
```bash
cd /var/www/course-management
python3 -m venv venv
source venv/bin/activate
```

### Установить зависимости
```bash
pip install -r requirements.txt
pip install gunicorn
```

## 🗄️ Шаг 3: Настройка базы данных

### Для production используйте PostgreSQL

#### Установить PostgreSQL
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql
brew services start postgresql
```

#### Создать базу данных
```bash
createdb course_management
createuser course_user
psql -d course_management
```

```sql
ALTER USER course_user WITH PASSWORD 'strong_password';
ALTER ROLE course_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE course_management TO course_user;
\q
```

#### Обновить app.py
```python
# Измените строку с SQLALCHEMY_DATABASE_URI на:
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://course_user:strong_password@localhost/course_management'
```

## 🌐 Шаг 4: Запуск приложения

### Создать systemd сервис

#### Создать файл `/etc/systemd/system/course-management.service`
```ini
[Unit]
Description=Course Management Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/course-management
Environment="PATH=/var/www/course-management/venv/bin"
ExecStart=/var/www/course-management/venv/bin/gunicorn \
    -w 4 \
    -b 127.0.0.1:8000 \
    --log-level=info \
    wsgi:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Запустить сервис
```bash
sudo systemctl daemon-reload
sudo systemctl start course-management
sudo systemctl enable course-management
sudo systemctl status course-management
```

## 🔒 Шаг 5: Настройка nginx

### Создать конфиг `/etc/nginx/sites-available/course-management`
```nginx
upstream course_management {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Редирект на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL сертификаты (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Безопасность SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Сжатие
    gzip on;
    gzip_types text/plain text/css application/json;

    # Логи
    access_log /var/log/nginx/course-management.access.log;
    error_log /var/log/nginx/course-management.error.log;

    # Основная конфигурация
    location / {
        proxy_pass http://course_management;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Увеличить timeout для больших запросов
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static файлы (если есть)
    location /static/ {
        alias /var/www/course-management/static/;
        expires 1w;
    }

    # Максимальный размер upload
    client_max_body_size 16M;
}
```

### Активировать конфиг
```bash
sudo ln -s /etc/nginx/sites-available/course-management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔐 Шаг 6: SSL сертификат (Let's Encrypt)

### Установить certbot
```bash
sudo apt install certbot python3-certbot-nginx
# или
brew install certbot
```

### Получить сертификат
```bash
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com
```

### Автоматическое обновление
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

## 📊 Шаг 7: Мониторинг и логирование

### Просмотр логов приложения
```bash
sudo journalctl -u course-management -f
```

### Просмотр логов nginx
```bash
tail -f /var/log/nginx/course-management.access.log
tail -f /var/log/nginx/course-management.error.log
```

### Мониторинг производительности
```bash
# Установить monitoring
sudo apt install htop nload iotop

# Проверить ресурсы
htop
```

## 🔄 Шаг 8: Резервные копии

### Автоматическое бэкапирование БД
```bash
#!/bin/bash
# /usr/local/bin/backup_courses.sh

BACKUP_DIR="/var/backups/course-management"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# PostgreSQL backup
pg_dump -U course_user course_management | \
    gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep only last 30 backups
find $BACKUP_DIR -type f -name "db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/db_$DATE.sql.gz"
```

### Добавить в crontab
```bash
sudo crontab -e
# Добавить строку для ежедневного бэкапа в 2:00 ночи
0 2 * * * /usr/local/bin/backup_courses.sh
```

## 🧪 Шаг 9: Тестирование после deployment

### Проверить доступность
```bash
curl -I https://your-domain.com
```

### Запустить функциональные тесты
```bash
cd /var/www/course-management
source venv/bin/activate
pytest test_app.py -v
```

## 🔍 Шаг 10: Продвинутая конфигурация

### Environment переменные
```bash
# Создать файл /var/www/course-management/.env
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
SQLALCHEMY_DATABASE_URI=postgresql://course_user:password@localhost/course_management
```

### Настройка Gunicorn
```bash
# Оптимизация для вашей системы
# В /etc/systemd/system/course-management.service
ExecStart=/var/www/course-management/venv/bin/gunicorn \
    -w $(nproc) \
    -k uvicorn \
    -b 127.0.0.1:8000 \
    --log-level info \
    --access-logfile /var/log/course-management/access.log \
    --error-logfile /var/log/course-management/error.log \
    wsgi:app
```

## 📈 Масштабирование

### Для большой нагрузки используйте:

1. **Load Balancing (HAProxy, Nginx)**
   ```bash
   # Несколько экземпляров приложения
   - course-management:8001
   - course-management:8002
   - course-management:8003
   ```

2. **Кэширование (Redis)**
   ```bash
   pip install redis
   # Кэшировать часто используемые запросы
   ```

3. **Асинхронные задачи (Celery)**
   ```bash
   pip install celery
   # Генерация отчётов в background
   ```

4. **CDN для статических файлов**
   ```bash
   # CloudFlare, Cloudinary, и т.д.
   ```

## 🛡️ Безопасность

### Обновить Flask
```python
# В app.py добавьте:
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
```

### Шифрование БД
```sql
-- PostgreSQL шифрование
CREATE EXTENSION pgcrypto;
```

### Аудит безопасности
```bash
# Проверить открытые порты
sudo netstat -tuln

# Проверить firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 🚨 Решение проблем при развёртывании

### Проблема: Permission denied
```bash
sudo chown -R www-data:www-data /var/www/course-management
sudo chmod -R 755 /var/www/course-management
```

### Проблема: 502 Bad Gateway
```bash
# Проверить statatus сервиса
sudo systemctl status course-management
# Перезагрузить
sudo systemctl restart course-management
```

### Проблема: Database connection error
```bash
# Проверить PostgreSQL
sudo -u postgres psql -l
# Проверить credentials в app.py
```

### Проблема: Static files not loading
```bash
# Собрать static файлы
python manage.py collectstatic
# Проверить nginx конфиг
sudo nginx -t
```

## 📚 Полезные команды

```bash
# Просмотр статуса приложения
sudo systemctl status course-management

# Перезагрузка приложения
sudo systemctl restart course-management

# Просмотр логов
sudo journalctl -u course-management -n 50

# Перезагрузка nginx
sudo systemctl reload nginx

# Проверка конфига nginx
sudo nginx -t

# Просмотр процессов Python
ps aux | grep gunicorn

# Проверка портов
sudo lsof -i :8000
sudo lsof -i :443
```

## ✅ Финальный чек-лист

- [ ] Python 3.8+ установлен
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] База данных настроена (PostgreSQL)
- [ ] Systemd сервис создан
- [ ] nginx сконфигурирован
- [ ] SSL сертификат установлен
- [ ] Firewall настроен
- [ ] Логирование работает
- [ ] Бэкапы настроены
- [ ] Тесты проходят успешно
- [ ] Приложение доступно по HTTPS

**Готово к production!** 🎉

---

## 📞 Поддержка

При проблемах проверьте:
1. Логи systemd: `journalctl -u course-management -f`
2. Логи nginx: `/var/log/nginx/course-management.error.log`
3. Статус сервиса: `systemctl status course-management`
4. Подключение БД: `psql -U course_user -d course_management`

Для production поддержки используйте Sentry для отслеживания ошибок.
