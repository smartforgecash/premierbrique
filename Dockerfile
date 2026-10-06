FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# staticfiles/ is gitignored, so the manifest must be built into the image.
# collectstatic touches no database; runtime secrets are supplied by Railway.
RUN DJANGO_SECRET_KEY=build-only-not-a-real-key DEBUG=false BUILDING_STATIC=true \
    python manage.py collectstatic --noinput

# Railway runs migrations once via railway.json before deploying the image.
CMD exec gunicorn premierbrique.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
