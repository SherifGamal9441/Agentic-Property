FROM python:3.11-slim

RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY docker/data-service-requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY docker/crontab /app/crontab
RUN echo "" >> /app/crontab && crontab /app/crontab

CMD ["sh", "-c", "python -m src.data_service.seed && cron && uvicorn src.data_service.app:app --host 0.0.0.0 --port 8000"]