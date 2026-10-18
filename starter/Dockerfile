# Lightweight image for LOCAL development. app.py runs Flask's dev server
# (debug on, bound to 0.0.0.0), so don't use this image in production.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend
COPY frontend frontend
COPY pytest.ini .

EXPOSE 5000

CMD ["python", "-m", "backend.app"]
