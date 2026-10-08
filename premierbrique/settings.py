import os
from pathlib import Path
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent

# Load a local .env file into environment variables if present (simple, safe parser)
env_path = BASE_DIR / ".env"
if env_path.exists():
    try:
        with env_path.open() as _f:
            for _raw in _f:
                _line = _raw.strip()
                if not _line or _line.startswith("#"):
                    continue
                if "=" not in _line:
                    continue
                _k, _v = _line.split("=", 1)
                _v = _v.strip()
                if len(_v) >= 2 and ((_v[0] == _v[-1]) and _v.startswith(("'", '"'))):
                    _v = _v[1:-1]
                os.environ.setdefault(_k.strip(), _v)
    except Exception:
        # Do not fail settings import if .env parsing has issues
        pass

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "replace-me-before-production")
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"
BUILDING_STATIC = os.environ.get("BUILDING_STATIC", "false").lower() == "true"
SITE_URL = os.environ.get("SITE_URL", "").strip().rstrip("/")
RAILWAY_PUBLIC_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()

if not DEBUG and not BUILDING_STATIC:
    if not os.environ.get("DJANGO_SECRET_KEY"):
        raise ImproperlyConfigured("DJANGO_SECRET_KEY is required in production.")
    if not os.environ.get("DATABASE_URL"):
        raise ImproperlyConfigured("DATABASE_URL is required in production.")

site_hostname = ""
if SITE_URL:
    parsed_site_url = urlsplit(SITE_URL)
    if parsed_site_url.scheme not in {"http", "https"} or not parsed_site_url.hostname:
        raise ImproperlyConfigured("SITE_URL must be an absolute http(s) URL.")
    site_hostname = parsed_site_url.hostname

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver", "healthcheck.railway.app"]
for host in [RAILWAY_PUBLIC_DOMAIN, site_hostname, *os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")]:
    host = host.strip()
    if host and host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)

CSRF_TRUSTED_ORIGINS = []
for origin in [SITE_URL, f"https://{RAILWAY_PUBLIC_DOMAIN}" if RAILWAY_PUBLIC_DOMAIN else "", *os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")]:
    origin = origin.strip().rstrip("/")
    if origin and origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "investments",
    "social_django",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
]

ROOT_URLCONF = "premierbrique.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "premierbrique.context_processors.analytics",
            ],
        },
    },
]

WSGI_APPLICATION = "premierbrique.wsgi.application"

if os.environ.get("DATABASE_URL"):
    import dj_database_url

    # Serverless hosts (Vercel) need conn_max_age=0: persistent connections pile up
    # per function instance and exhaust the database's connection limit.
    # Long-running hosts (Cloud Run, a VPS) want 600.
    DATABASES = {
        "default": dj_database_url.config(
            conn_max_age=int(os.environ.get("DB_CONN_MAX_AGE", "600")),
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "social_core.backends.google.GoogleOAuth2",
]

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {"prompt": "select_account"}
# Start OAuth with a CSRF-protected POST, matching current social-auth releases.
SOCIAL_AUTH_REQUIRE_POST = True

SOCIAL_AUTH_LOGIN_REDIRECT_URL = "/account/"
SOCIAL_AUTH_LOGIN_ERROR_URL = "/login.html"

SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.dummy.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Premier Brique <no-reply@premierbrique.com>")

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "css", BASE_DIR / "js"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
CARD_PAYMENTS_ENABLED = os.environ.get("CARD_PAYMENTS_ENABLED", "true").lower() == "true"
STRIPE_BANK_ACCOUNT_HOLDER_NAME = os.environ.get("STRIPE_BANK_ACCOUNT_HOLDER_NAME", "")
BANK_TRANSFER_ACCOUNT_HOLDER = os.environ.get("BANK_TRANSFER_ACCOUNT_HOLDER", "")
BANK_TRANSFER_IBAN = os.environ.get("BANK_TRANSFER_IBAN", "")
BANK_TRANSFER_BIC = os.environ.get("BANK_TRANSFER_BIC", "")
BANK_TRANSFER_BANK_NAME = os.environ.get("BANK_TRANSFER_BANK_NAME", "")
# Retained only to reconcile payments initiated before the SumUp switch.
MOLLIE_API_KEY = os.environ.get("MOLLIE_API_KEY", "").strip()
SUMUP_API_KEY = os.environ.get("SUMUP_API_KEY", "").strip()
SUMUP_MERCHANT_CODE = os.environ.get("SUMUP_MERCHANT_CODE", "").strip()
GOOGLE_ANALYTICS_ID = os.environ.get("GOOGLE_ANALYTICS_ID", "").strip()

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/login.html"
LOGIN_REDIRECT_URL = "/account/"
LOGOUT_REDIRECT_URL = "/"
