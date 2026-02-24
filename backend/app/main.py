from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, ingest, health
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="TaxGPT Financial Chatbot",
    description="Hybrid RAG chatbot combining vector search + knowledge graph for financial Q&A",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(ingest.router, prefix="/api", tags=["Ingestion"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    pass
