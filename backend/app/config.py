from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    voyage_api_key: str = ""

    # Embedding Configuration
    embedding_provider: str = "voyage"  # voyage | openai | local
    embedding_model: str = "voyage-finance-2"

    # Storage
    chroma_persist_dir: str = "./data/chroma_db"
    graph_persist_path: str = "./data/graph.pkl"

    # Logging
    log_level: str = "INFO"

    # LLM Provider (openai or anthropic)
    llm_provider: str = "openai"

    # LLM Model (gpt-4o for OpenAI, claude-sonnet-4-20250514 for Anthropic)
    llm_model: str = "gpt-4o"

    # Chunking
    chunk_size: int = 500
    chunk_overlap: int = 50

    # Low Memory Mode (for 8GB machines)
    low_memory_mode: bool = True  # Enable by default for safety

    # Low memory settings
    low_memory_max_workers: int = 2  # Parallel workers (vs 8 in normal mode)
    low_memory_page_batch_size: int = 50  # Pages to process before clearing memory
    low_memory_embedding_batch_size: int = 32  # Embeddings per API call
    low_memory_vector_batch_size: int = 500  # Chunks per ChromaDB insert

    # Normal mode settings
    normal_max_workers: int = 8
    normal_embedding_batch_size: int = 128
    normal_vector_batch_size: int = 5000

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def max_workers(self) -> int:
        """Get max workers based on memory mode."""
        return self.low_memory_max_workers if self.low_memory_mode else self.normal_max_workers

    @property
    def embedding_batch_size(self) -> int:
        """Get embedding batch size based on memory mode."""
        return self.low_memory_embedding_batch_size if self.low_memory_mode else self.normal_embedding_batch_size

    @property
    def vector_batch_size(self) -> int:
        """Get vector store batch size based on memory mode."""
        return self.low_memory_vector_batch_size if self.low_memory_mode else self.normal_vector_batch_size


@lru_cache
def get_settings() -> Settings:
    return Settings()
