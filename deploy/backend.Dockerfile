FROM ${PYTHON_IMAGE:-python:3.11-slim} as base

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy code
COPY . /app

# Virtualenv not required in container
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt || true

# Expose Flask port
EXPOSE 5003

# UTF-8 logs to avoid cp1252 errors
ENV PYTHONIOENCODING=utf-8 \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

CMD ["python", "simple_diary_api.py"]


