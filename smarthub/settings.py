from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env from project root (same folder as manage.py)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------------
# Core
# -------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# Hackathon-safe: allow all hosts so tunnel URLs work (Cloudflare/ngrok)
# For production, set ALLOWED_HOSTS via env and remove ["*"].
ALLOWED_HOSTS = ["*"]

# If you want a stricter version (optional), comment the above and use:
# ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")


# -------------------------
# Apps
# -------------------------
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "corsheaders",
    # Optional Swagger/OpenAPI (only if installed)
    "drf_spectacular",

    # Local apps
    "accounts",
    "dashboard",
    "farms",
    "sensors",
    "weather",
    "disease",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # should be high
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "smarthub.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "smarthub.wsgi.application"


# -------------------------
# Database (SQLite demo)
# -------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# -------------------------
# Password validation
# -------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# -------------------------
# Locale
# -------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True


# -------------------------
# Static + Media
# -------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# If you have a /static folder in root, this helps during development
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# -------------------------
# Auth redirects
# -------------------------
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/accounts/login/"


# -------------------------
# DRF
# -------------------------
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    # keep JSON only (clean). Uncomment BrowsableAPIRenderer if you want DRF UI.
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


# -------------------------
# Swagger/OpenAPI (drf-spectacular)
# -------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "Smart Agri API",
    "DESCRIPTION": "IoT + Weather + AI Disease Detection + Advisories",
    "VERSION": "1.0.0",
}


# -------------------------
# CORS (development)
# -------------------------
CORS_ALLOW_ALL_ORIGINS = True


# -------------------------
# Tunnel / HTTPS proxy support
# (helps CSRF + scheme when behind Cloudflare/ngrok)
# -------------------------
CSRF_TRUSTED_ORIGINS = [
    "https://*.trycloudflare.com",
    "https://*.ngrok-free.app",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True


# -------------------------
# Weather API key (optional)
# -------------------------
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")