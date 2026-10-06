"""Create an admin only when explicit credentials are supplied."""

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "premierbrique.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402


username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
if not username or not email or not password:
    raise SystemExit("DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD are required.")

User = get_user_model()
if User.objects.filter(username=username).exists():
    print("Superuser already exists; password was not changed.")
else:
    User.objects.create_superuser(username, email, password)
    print("Superuser created.")
