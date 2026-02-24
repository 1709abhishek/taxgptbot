FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including LibreOffice for old .ppt support)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY data ./data

# Create data directories
RUN mkdir -p data/raw data/chroma_db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
