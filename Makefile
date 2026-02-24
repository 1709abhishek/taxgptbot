.PHONY: install dev test eval deploy clean backend frontend build

# Install all dependencies
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# Run development servers (docker)
dev:
	docker-compose up

# Run backend only (local)
backend:
	cd backend && uvicorn app.main:app --reload --port 8000

# Run frontend only (local)
frontend:
	cd frontend && npm run dev

# Run tests
test:
	cd backend && pytest tests/ -v

# Run evaluation
eval:
	cd backend && python -m scripts.evaluate

# Build for production
build:
	docker-compose build

# Deploy to Railway
deploy:
	railway up

# Clean up
clean:
	docker-compose down -v
	rm -rf backend/data/chroma_db/*
	rm -rf backend/data/graph.pkl
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Ingest sample data
ingest:
	cd backend && python -m scripts.ingest_data

# Format code
format:
	cd backend && black app/ tests/
	cd frontend && npm run format

# Lint code
lint:
	cd backend && ruff check app/
	cd frontend && npm run lint
