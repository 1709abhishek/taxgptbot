FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies + git-lfs for large files
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git-lfs \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/app ./app

# Copy pre-built data (ChromaDB + graph)
COPY backend/data ./data

ENV PORT=8000
EXPOSE 8000

CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"
