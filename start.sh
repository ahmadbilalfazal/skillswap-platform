#!/bin/sh
set -e

# Run migrations and collectstatic against the runtime DATABASE_URL
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Start Gunicorn
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
