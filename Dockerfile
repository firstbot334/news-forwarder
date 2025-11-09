FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data

# Default envs (override in your own .env or Railway/Render/Heroku)
ENV POLL_INTERVAL=600     DB_PATH=/app/data/state.sqlite

CMD ["python", "-m", "app.main"]
