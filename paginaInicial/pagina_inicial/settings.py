import json
import os
from pathlib import Path
from typing import Any, Dict, List

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-placeholder")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
_allowed_hosts = os.environ.get("ALLOWED_HOSTS", "*")
ALLOWED_HOSTS: List[str] = [host.strip() for host in _allowed_hosts.split(",") if host.strip()] or ["*"]

_csrf_origins_env = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
_default_csrf_origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
]
if _csrf_origins_env:
    _default_csrf_origins.extend(origin.strip() for origin in _csrf_origins_env.split(","))
CSRF_TRUSTED_ORIGINS = [
    origin.rstrip("/")
    for origin in _default_csrf_origins
    if origin.strip()
]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "portal",
    "agenda",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pagina_inicial.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "pagina_inicial.wsgi.application"

# Database (SQLite by default, override via DATABASE_URL)
_default_database: Dict[str, Any] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": BASE_DIR / "db.sqlite3",
}

DATABASES: Dict[str, Dict[str, Any]] = {"default": _default_database}

_database_url = os.environ.get("DATABASE_URL")
if _database_url:
    conn_max_age = int(os.environ.get("DATABASE_CONN_MAX_AGE", "600"))
    ssl_require = os.environ.get("DATABASE_SSL_REQUIRE", "false").lower() == "true"
    DATABASES["default"] = dj_database_url.parse(
        _database_url,
        conn_max_age=conn_max_age,
        ssl_require=ssl_require,
    )

# Use signed cookies so we do not depend on a database for sessions
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

# Password validation (not used, but kept for completeness)
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "portal:login"
PORTAL_USERS_PATH = Path(os.environ.get("PORTAL_USERS_PATH", BASE_DIR / "users" / "users.json"))

PROFILE_RULES: Dict[str, Dict[str, Any]] = {
    "admin": {"label": "Administrador", "can_configure": True},
    "normal": {"label": "Operador", "can_configure": True},
    "viewer": {"label": "Visualizador", "can_configure": False},
}

DEFAULT_PROFILE = "viewer"
ALL_PROFILES = tuple(PROFILE_RULES.keys())


def load_valid_users() -> Dict[str, Dict[str, str]]:
    """Load valid user definitions from the JSON file."""
    if PORTAL_USERS_PATH.exists():
        with PORTAL_USERS_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            if data:
                normalised: Dict[str, Dict[str, str]] = {}
                for key, value in data.items():
                    profile = value.get("profile", DEFAULT_PROFILE).lower()
                    if profile not in PROFILE_RULES:
                        profile = DEFAULT_PROFILE
                    normalised[key.lower()] = {
                        "token": value.get("token", ""),
                        "profile": profile,
                    }
                return normalised
    return {
        "daianapaulasales@gmail.com": {"token": "12345", "profile": "admin"},
        "cmota.dev@gmail.com": {"token": "12345", "profile": "normal"},
        "visualizacao@example.com": {"token": "12345", "profile": "viewer"},
    }


VALID_USERS = load_valid_users()

# List of portal pages available in the UI
PAGINAS = [
    {"titulo": "Informativo do Congresso (em construção)", "url": "/redirect/informativo", "roles": "admin"},
    {"titulo": "Agenda da Semana", "url": "/redirect/agenda", "roles": ("admin", "normal")},
    {"titulo": "Requerimentos", "url": "/redirect/requerimentos", "roles": ("admin", "normal", "viewer")},
    {"titulo": "Matérias em Tramitação nas Comissões (Senado)", "url": "/redirect/comissoes_senado", "roles": ALL_PROFILES},
    {"titulo": "Matérias em Tramitação nas Comissões Mistas", "url": "/redirect/comissoes_mistas", "roles": ALL_PROFILES},
    {"titulo": "Matérias em Tramitação nas Comissões (Câmara)", "url": "/redirect/comissoes_camara", "roles": ALL_PROFILES},
    {"titulo": "Matérias Prioritárias", "url": "/redirect/materias_prioritarias", "roles": ALL_PROFILES},
    {"titulo": "Busca Avançada em Proposições", "url": "/redirect/busca_avancada", "roles": ALL_PROFILES},
    {"titulo": "Busca de Processos SEI", "url": "/redirect/busca_sei", "roles": ("admin", "normal")},
    {"titulo": "Nuvem de Palavras (em construção)", "url": "", "roles": ("admin", "normal")},
    {"titulo": "Análise de Votações (em construção)", "url": "", "roles": ("admin", "normal")},
    {"titulo": "Classificação Automatizada de Proposições (em construção)", "url": "", "roles": ("admin", "normal")},
    {"titulo": "Acompanhamento de Sanção e Veto (em construção)", "url": "", "roles": ("admin", "normal")},
]

PORTAL_APP_BASE_URL = "http://127.0.0.1:8080"


def _with_app_base(path: str) -> str:
    if not PORTAL_APP_BASE_URL:
        return path
    if not path.startswith("/"):
        return f"{PORTAL_APP_BASE_URL}/{path}"
    return f"{PORTAL_APP_BASE_URL}{path}"


REDIRECT_URLS = {
    "informativo": "/informativo/",
    "agenda": _with_app_base("/busca-eventos/"),
    "requerimentos": _with_app_base("/busca-reqs/"),
    "comissoes_senado": _with_app_base("/busca-comissoes-sf/"),
    "comissoes_mistas": _with_app_base("/busca-comissoes-mistas/"),
    "comissoes_camara": _with_app_base("/busca-comissoes-cd/"),
    "materias_prioritarias": _with_app_base("/busca-materias/"),
    "busca_avancada": _with_app_base("/base-pl/"),
    "busca_sei": _with_app_base("/busca-sei/"),
}

# Celery Configuration
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Sao_Paulo"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
