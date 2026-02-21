FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN DJANGO_ENV=production SECRET_KEY=build-placeholder python manage.py collectstatic --noinput 2>/dev/null || true

# Create startup script that runs migrations, seeds data, then starts gunicorn
RUN printf '#!/bin/bash\nset -e\npython manage.py migrate --no-input\npython manage.py seed_game_content 2>&1 || echo "WARN: seed_game_content failed"\npython manage.py seed_achievements 2>&1 || echo "WARN: seed_achievements failed"\npython manage.py seed_feed_content 2>&1 || echo "WARN: seed_feed_content failed"\nexec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120\n' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
