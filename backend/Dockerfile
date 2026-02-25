FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gdown for Google Drive downloads
RUN pip install gdown

# Copy application code
COPY backend/app ./app

# Download pre-built data from Google Drive
RUN mkdir -p data && \
    gdown "1qiCbwuwx42Eqyzw9mGL5r6MOt3DxDF49" -O /tmp/data.tar.gz && \
    tar -xzf /tmp/data.tar.gz -C data && \
    rm /tmp/data.tar.gz

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
