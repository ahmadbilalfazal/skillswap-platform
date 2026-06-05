#!/bin/sh
set -e

# Run migrations and collectstatic against the runtime DATABASE_URL
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Optional demo seed for environments like Render free tier where shell access is unavailable.
# Enable by setting SEED_DEMO_ON_START=1 in service environment variables.
if [ "$SEED_DEMO_ON_START" = "1" ]; then
	python manage.py seed_demo_10
fi

# Start Gunicorn
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
