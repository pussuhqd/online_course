"""
Конфигурация приложения
"""

import os
from datetime import timedelta

class Config:
    """Базовая конфигурация"""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_REFRESH_EACH_REQUEST = True
    
    # API
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    DATABASE_URL = 'sqlite:///courses.db'


class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Конфигурация для production"""
    DEBUG = False
    TESTING = False


# Выбор конфигурации
ENV = os.environ.get('FLASK_ENV', 'development')

if ENV == 'testing':
    config = TestingConfig
elif ENV == 'production':
    config = ProductionConfig
else:
    config = DevelopmentConfig
