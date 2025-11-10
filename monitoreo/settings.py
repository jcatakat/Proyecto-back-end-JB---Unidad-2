# monitoreo/settings.py
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carga .env desde la raíz del proyecto
load_dotenv(BASE_DIR / ".env")

# --- Configuración base ---
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-unsafe")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Apps del proyecto
    "organizations",
    "dispositivos",
    "accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "monitoreo.urls"
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "monitoreo.wsgi.application"

# --- Base de datos (MySQL en RDS con SSL) ---
ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()

if ENGINE == "mysql":
    # Depende de mysqlclient (MySQLdb). El warning de Pylance en VSCode es visual, no afecta en servidor.
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")

    # Ruta del bundle CA de RDS (debe existir en el EC2)
    DB_SSL_CA = os.getenv("DB_SSL_CA", "/etc/ssl/certs/aws-rds/rds-combined-ca-bundle.pem")
    SSL_OPTIONS = {"ca": DB_SSL_CA} if DB_SSL_CA else None

    # Construimos OPTIONS y forzamos agregar ssl si hay CA
    DB_OPTIONS = {"charset": "utf8mb4"}
    if SSL_OPTIONS:
        DB_OPTIONS["ssl"] = SSL_OPTIONS

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": DB_NAME,
            "USER": DB_USER,
            "PASSWORD": DB_PASSWORD,
            "HOST": DB_HOST,
            "PORT": DB_PORT,
            "OPTIONS": DB_OPTIONS,
        }
    }

    # Chequeo defensivo: si RDS exige SSL y no tenemos CA, avisa claramente
    if "ssl" not in DATABASES["default"]["OPTIONS"]:
        raise RuntimeError("Falta configurar DB_SSL_CA para conexión SSL a RDS (requerido).")
else:
    # Fallback solo para desarrollo local (no se usa en tu evaluación)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / os.getenv("DB_NAME", "db.sqlite3"),
        }
    }

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

from django.contrib.messages import constants as msg
MESSAGE_TAGS = {
    msg.DEBUG:   "secondary",
    msg.INFO:    "info",
    msg.SUCCESS: "success",
    msg.WARNING: "warning",
    msg.ERROR:   "danger",
}

# Sesión (opcional)
SESSION_COOKIE_AGE = 60 * 60 * 2
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = False
# Para prod con HTTPS:
# SESSION_COOKIE_SECURE = True
# SESSION_COOKIE_SAMESITE = 'Lax'
