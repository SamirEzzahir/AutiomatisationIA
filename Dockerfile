# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copier les dépendances en premier (optimisation cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY app.py .

ARG APP_VERSION=1.0
ENV APP_VERSION=$APP_VERSION

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
