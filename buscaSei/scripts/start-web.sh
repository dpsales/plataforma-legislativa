#!/bin/bash
set -e

cd /app

# Execute migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn busca_sei.wsgi:application --bind 0.0.0.0:8080 --workers 3 --timeout 120
