import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-vin0b(3y&5du!aaheh0pbq_%-vspi0g1%e@8e^wn%&ju$=u30g"
DEBUG = True
ALLOWED_HOSTS = []


INSTALLED_APPS = [
    # 🎨 Admin moderne
    "jazzmin",

    "colorfield",
    # "admin_interface",  # ⚠️ désactivé car conflit possible avec Jazzmin

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "messenger.apps.MessengerConfig",

    # Apps internes
    "notifications.apps.NotificationsConfig",
    "core.apps.CoreConfig",
    "programs",
    "admissions.apps.AdmissionsConfig",
    "blog",
    "campuses",
    'users.apps.UsersConfig',
    'django_cotton',
    "news",
    "gallery",
    "dashboard",
    "masters.apps.MastersConfig",

    # Outils externes
    "django_ckeditor_5",
    "django_cleanup.apps.CleanupConfig",
    "crispy_forms",
    "crispy_tailwind",

    'rest_framework',
    'masters.api_teacher',
]



REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
}



# Crispy forms (tailwind)
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# CKEditor
CKEDITOR_5_CONFIGS = {
    "default": {
        "language": "fr",
        "toolbar": [
            "heading","|","bold","italic","underline","link","bulletedList","numberedList",
            "blockQuote","insertTable","imageUpload","mediaEmbed","codeBlock","|",
            "alignment","outdent","indent","|","undo","redo","|","removeFormat","|",
            "findAndReplace"
        ],
        "image": {"toolbar": ["imageTextAlternative","imageStyle:full","imageStyle:side"]},
        "table": {"contentToolbar": ["tableColumn","tableRow","mergeTableCells"]},
        "mediaEmbed": {"previewsInData": True},
    }
}
CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "masters.middleware.MasterAccessMiddleware",  # ← ajoute-le ici

]




ROOT_URLCONF = "config.urls"

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
                "core.context_processors.site_basics",
                "notifications.context_processors.unread_notifications_count",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Base de données
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Sécurité des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalisation
LANGUAGE_CODE = "fr-FR"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Statics et médias
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.CustomUser"

# ✅ Login / logout redirections
LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "/dashboard/"   # <-- redirection vers ton dashboard
LOGOUT_REDIRECT_URL = "users:login"

# Emails (dev → console)
DEFAULT_FROM_EMAIL = "no-reply@esfe-mali.org"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# 🎨 Jazzmin settings
JAZZMIN_SETTINGS = {
    "site_title": "ESFé Mali Admin",
    "site_header": "ESFé Mali",
    "site_brand": "ESFé Dashboard",
    "welcome_sign": "Bienvenue sur le panneau d'administration",
    "copyright": "© ESFé Mali",
    "show_sidebar": True,
    "navigation_expanded": True,
    "topmenu_links": [
        {"name": "Accueil", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Site public", "url": "/", "new_window": True},
    ],
    "icons": {
        # Admissions
        "admissions.admission": "fas fa-user-graduate",
        "admissions.paymenttransaction": "fas fa-credit-card",
        "admissions.webhookevent": "fas fa-plug",

        # Programmes
        "programs.program": "fas fa-book-open",
        "programs.cycle": "fas fa-layer-group",

        # Utilisateurs
        "users.customuser": "fas fa-user-cog",
        "auth.group": "fas fa-users",

        # Notifications
        "notifications.notification": "fas fa-bell",

        # Blog
        "blog.post": "fas fa-file-alt",
        "blog.comment": "fas fa-comments",
        "blog.category": "fas fa-tags",
        "blog.reaction": "fas fa-thumbs-up",

        # Campus
        "campuses.campus": "fas fa-school",

        # Galerie
        "gallery.album": "fas fa-images",
        "gallery.media": "fas fa-photo-video",

        # News
        "news.news": "fas fa-newspaper",
        "news.newsmedia": "fas fa-photo-video",

        # Dashboard
        "dashboard.dashboardlog": "fas fa-history",
    },
}

# 🎨 Jazzmin UI tweaks (personnalisation thème ESFé)
JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",             # clair par défaut
    "dark_mode_theme": "darkly",   # switch Dark/Light
    "navbar": "navbar-dark bg-primary",
    "sidebar": "sidebar-dark-primary",
    "brand": "bg-primary",
    "accent": "accent-cyan",
    "body_small_text": False,
    "footer_fixed": False,
    "theme_color": "#0f172a",      # Bleu nuit ESFé
    "button_classes": {
        "primary": "btn-primary bg-cyan-600 border-cyan-700",
        "secondary": "btn-secondary bg-slate-600 border-slate-700",
        "info": "btn-info bg-cyan-500 border-cyan-600",
        "warning": "btn-warning bg-yellow-500 border-yellow-600",
        "danger": "btn-danger bg-red-600 border-red-700",
    },
}


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@esfe-mali.org"

ASGI_APPLICATION = "config.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
    },
}

