FROM python:3.11-slim

WORKDIR /app

# Install system dependencies + git-lfs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    git-lfs \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/app ./app

# Clone repo and pull LFS files for data (workaround for Railway not pulling LFS)
RUN git clone --depth 1 https://github.com/1709abhishek/taxgptbot.git /tmp/repo \
    && cd /tmp/repo \
    && git lfs pull \
    && cp -r /tmp/repo/backend/data ./data \
    && rm -rf /tmp/repo

ENV PORT=8000
EXPOSE 8000

CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"
