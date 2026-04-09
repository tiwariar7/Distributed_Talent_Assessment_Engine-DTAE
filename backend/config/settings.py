"""
Django settings for the Distributed Talent Assessment Engine.

Relational data lives in PostgreSQL (3NF, ACID).
Unstructured execution artifacts live in CouchDB (MVCC, MapReduce views).
"""

from datetime import timedelta
from pathlib import Path

import environ
from kombu import Exchange, Queue

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DOCKER_EXECUTOR_TIMEOUT_SECONDS=(int, 10),
    DOCKER_EXECUTOR_MEMORY_MB=(int, 128),
)

environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "daphne",
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.organizations",
    "apps.accounts",
    "apps.assessments",
    "apps.executions",
    "apps.leaderboard",
    "apps.recruiter",
    "apps.health",
    "apps.dsa_intelligence",
    "apps.proctoring",
    "channels",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "config.prometheus_middleware.PrometheusMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "frontend" / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379/0")],
        },
    },
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="dtae"),
        "USER": env("POSTGRES_USER", default="dtae"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="dtae_secret"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "frontend" / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": env("THROTTLE_USER_RATE", default="200/hour"),
        "submission": env("THROTTLE_SUBMISSION_RATE", default="10/min"),
        "login": env("THROTTLE_LOGIN_RATE", default="5/min"),
        "jwt_abuse": env("THROTTLE_JWT_ABUSE_RATE", default="10/min"),
        "recruiter_api": env("THROTTLE_RECRUITER_RATE", default="500/hour"),
        "anti_dos": env("THROTTLE_DOS_RATE", default="100/sec"),
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int("JWT_ACCESS_MINUTES", default=60),
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env.int("JWT_REFRESH_DAYS", default=7),
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_CACHE_URL", default="redis://localhost:6379/1"),
    },
}

# CouchDB (document store — not registered in DATABASES)
COUCHDB_URL = env("COUCHDB_URL", default="http://localhost:5984")
COUCHDB_USER = env("COUCHDB_USER", default="admin")
COUCHDB_PASSWORD = env("COUCHDB_PASSWORD", default="dtae_secret")
COUCHDB_DATABASE = env("COUCHDB_DATABASE", default="dtae_documents")

# Redis (Cache, Channels layer)
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

# Celery Broker and Result Backend
CELERY_BROKER_URL = env("RABBITMQ_URL", default="amqp://guest:guest@localhost:5672//")
CELERY_RESULT_BACKEND = env("REDIS_CACHE_URL", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Queues topology definition
default_exchange = Exchange("default", type="direct")
dead_letter_exchange = Exchange("dead_letter", type="direct")

dl_args = {
    "x-dead-letter-exchange": "dead_letter",
    "x-dead-letter-routing-key": "dead_letter",
}

CELERY_TASK_QUEUES = (
    Queue("high_priority", default_exchange, routing_key="high", queue_arguments={**dl_args, "x-max-priority": 10}),
    Queue("medium_priority", default_exchange, routing_key="medium", queue_arguments={**dl_args, "x-max-priority": 5}),
    Queue("low_priority", default_exchange, routing_key="low", queue_arguments={**dl_args, "x-max-priority": 3}),
    Queue("maintenance", default_exchange, routing_key="maintenance"),
    Queue("dead_letter", dead_letter_exchange, routing_key="dead_letter"),
    # Language-specific queues for distributed routing
    Queue("lang_python", default_exchange, routing_key="python"),
    Queue("lang_cpp", default_exchange, routing_key="cpp"),
    Queue("lang_java", default_exchange, routing_key="java"),
    Queue("lang_javascript", default_exchange, routing_key="javascript"),
)

CELERY_TASK_DEFAULT_QUEUE = "high_priority"
CELERY_TASK_DEFAULT_EXCHANGE = "default"
CELERY_TASK_DEFAULT_ROUTING_KEY = "high"

CELERY_TASK_ROUTES = {
    "apps.executions.tasks.run_submission_evaluation": {
        "queue": "high_priority",
        "routing_key": "high",
    },
    "apps.leaderboard.tasks.update_leaderboard_task": {
        "queue": "medium_priority",
        "routing_key": "medium",
    },
    "apps.executions.tasks.recruiter_re_evaluation_task": {
        "queue": "low_priority",
        "routing_key": "low",
    },
    "apps.executions.tasks.cleanup_task": {
        "queue": "maintenance",
        "routing_key": "maintenance",
    },
}

# Docker sandbox
DOCKER_EXECUTOR_IMAGE = env(
    "DOCKER_EXECUTOR_IMAGE",
    default="dtae/multi-sandbox:latest",
)
DOCKER_EXECUTOR_TIMEOUT_SECONDS = env("DOCKER_EXECUTOR_TIMEOUT_SECONDS")
DOCKER_EXECUTOR_MEMORY_MB = env("DOCKER_EXECUTOR_MEMORY_MB")
DOCKER_HOST = env("DOCKER_HOST", default=None)

# Security Hardening
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"

# CORS configuration
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=True)
CORS_ALLOW_CREDENTIALS = True

# Content Security Policy (CSP)
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:")
CSP_CONNECT_SRC = ("'self'", "ws:", "wss:")

# Structured logging
LOG_LEVEL = env("LOG_LEVEL", default="INFO")
LOG_FORMAT = env("LOG_FORMAT", default="verbose")
from config.logging import build_logging_config  # noqa: E402

LOGGING = build_logging_config(LOG_LEVEL, LOG_FORMAT)

# Proctoring configuration
PROCTORING_MAX_WARNINGS = 2
PROCTORING_AUTO_SUBMIT_ON_VIOLATION = True


# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Enhance component rendering performance.

# Refactor: Refactor variable names for better readability.

# Refactor: Improve error handling and exception logging.

# Refactor: Enhance component rendering performance.
