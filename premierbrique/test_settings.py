"""Isolated test configuration: never connect to the deployed database or payment APIs."""
import os
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = ""
os.environ["DJANGO_SECRET_KEY"] = "test-only-not-a-production-secret"

from .settings import *  # noqa: F403, E402

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
SUMUP_API_KEY = ""
SUMUP_MERCHANT_CODE = ""
MOLLIE_API_KEY = ""
STRIPE_SECRET_KEY = ""
SECURE_SSL_REDIRECT = False
