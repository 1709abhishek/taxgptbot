FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/app ./app

# Download pre-built data from GitHub release
RUN mkdir -p data && \
    curl -L https://github.com/1709abhishek/taxgptbot/releases/download/v1.0.0/taxgpt-data.tar.gz -o /tmp/data.tar.gz && \
    tar -xzf /tmp/data.tar.gz -C data && \
    rm /tmp/data.tar.gz

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
