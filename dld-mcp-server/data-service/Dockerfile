FROM python:3.11-slim

RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY crontab /app/crontab
RUN echo "" >> /app/crontab && crontab /app/crontab

CMD ["sh", "-c", "python seed.py && cron && uvicorn main:app --host 0.0.0.0 --port 8000"]