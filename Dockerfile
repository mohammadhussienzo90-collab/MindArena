FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN DJANGO_ENV=production SECRET_KEY=build-placeholder python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

# Migrations and seed commands run via Railway releaseCommand (railway.toml).
# For non-Railway deployments, run them manually or via the Procfile release phase.
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"]
