FROM python:3.10-slim AS base

WORKDIR /app

# System dependencies for psycopg2, cryptography, Pillow, reportlab
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY database/ ./database/
COPY alembic.ini .

# Test files are included so `pytest unit_tests/` and `pytest api_tests/` work inside the container
COPY unit_tests/ ./unit_tests/
COPY api_tests/ ./api_tests/
COPY conftest.py .
COPY pytest.ini .

# Frontend dist is mounted at runtime via volume (see docker-compose.yml)
ENV FRONTEND_DIST_PATH=/app/frontend_dist

EXPOSE 8443

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8443", \
     "--ssl-certfile", "/certs/cert.pem", "--ssl-keyfile", "/certs/key.pem"]
