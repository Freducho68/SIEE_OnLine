import os

class Config:
    # ===== CONFIGURACIÓN DE BASE DE DATOS MYSQL =====
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "root")
    DB_NAME = os.environ.get("DB_NAME", "siee_db")
    DB_PORT = int(os.environ.get("DB_PORT", "3306"))

    # ===== CONFIGURACIÓN DE SESIÓN =====
    SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(32).hex())
    SESSION_PERMANENT = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # ===== CONFIGURACIÓN DE ENTORNO =====
    DEBUG = str(os.environ.get("FLASK_DEBUG", "0")).strip().lower() in ("1", "true", "yes", "on")
    TESTING = False

    # ===== INFORMACIÓN DE APP =====
    APP_NAME = "Sistema de Gestión Académica"
    APP_VERSION = "2.0.0"
