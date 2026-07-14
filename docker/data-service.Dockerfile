FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY docker/data-service-requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "python -m src.data_service.bootstrap && uvicorn src.data_service.app:app --host 0.0.0.0 --port 8000"]
