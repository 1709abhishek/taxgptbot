from typing import List, Generator, Callable, Optional
from functools import lru_cache
import gc
import time

from app.config import get_settings


class EmbeddingService:
    """
    Unified embedding service supporting multiple providers.
    Includes batch processing for efficient large-scale embedding.

    Supports low memory mode with smaller batch sizes.
    """

    # Provider-specific batch size limits (max allowed by API)
    PROVIDER_MAX_BATCH = {
        "voyage": 128,    # Voyage AI max per request
        "openai": 2048,   # OpenAI max per request
        "local": 64,      # Local model
    }

    def __init__(self, provider: str = None, model: str = None):
        settings = get_settings()
        self.provider = provider or settings.embedding_provider
        self.model_name = model or settings.embedding_model
        self.settings = settings

        self._client = None
        self._local_model = None

        # Use settings-based batch size, capped at provider max
        provider_max = self.PROVIDER_MAX_BATCH.get(self.provider, 64)
        self._batch_size = min(settings.embedding_batch_size, provider_max)

    @property
    def batch_size(self) -> int:
        """Get the optimal batch size for the current provider."""
        return self._batch_size

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []

        if self.provider == "voyage":
            return self._embed_voyage(texts)
        elif self.provider == "openai":
            return self._embed_openai(texts)
        else:
            return self._embed_local(texts)

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query."""
        return self.embed([text])[0]

    def embed_batched(
        self,
        texts: List[str],
        batch_size: int = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        delay_between_batches: float = 0.0,
        force_gc: bool = None,
    ) -> List[List[float]]:
        """
        Generate embeddings in batches for large datasets.

        Args:
            texts: List of texts to embed
            batch_size: Override default batch size (uses provider optimal if None)
            progress_callback: Optional callback(completed_count, total_count)
            delay_between_batches: Seconds to wait between API calls (rate limiting)
            force_gc: Force garbage collection after each batch (default: True in low_memory_mode)

        Returns:
            List of embeddings in same order as input texts
        """
        if not texts:
            return []

        batch_size = batch_size or self._batch_size
        total = len(texts)
        all_embeddings = []

        # Default GC behavior based on memory mode
        if force_gc is None:
            force_gc = self.settings.low_memory_mode

        for i, batch in enumerate(self._batch_generator(texts, batch_size)):
            # Embed the batch
            batch_embeddings = self.embed(batch)
            all_embeddings.extend(batch_embeddings)

            # Progress callback
            completed = min((i + 1) * batch_size, total)
            if progress_callback:
                progress_callback(completed, total)

            # Clean up batch reference and optionally force GC
            del batch_embeddings
            if force_gc and (i + 1) % 10 == 0:  # GC every 10 batches
                gc.collect()

            # Rate limiting delay (skip on last batch)
            if delay_between_batches > 0 and completed < total:
                time.sleep(delay_between_batches)

        return all_embeddings

    def embed_batched_generator(
        self,
        texts: List[str],
        batch_size: int = None,
    ) -> Generator[tuple, None, None]:
        """
        Generator that yields (batch_index, batch_texts, batch_embeddings).
        Useful for processing embeddings as they're generated.

        Yields:
            (batch_index, start_idx, batch_embeddings)
        """
        batch_size = batch_size or self._batch_size

        for i, batch in enumerate(self._batch_generator(texts, batch_size)):
            start_idx = i * batch_size
            batch_embeddings = self.embed(batch)
            yield (i, start_idx, batch_embeddings)

    def _batch_generator(
        self, texts: List[str], batch_size: int
    ) -> Generator[List[str], None, None]:
        """Split texts into batches."""
        for i in range(0, len(texts), batch_size):
            yield texts[i : i + batch_size]

    def _embed_voyage(self, texts: List[str]) -> List[List[float]]:
        """Embed using Voyage AI."""
        if self._client is None:
            import voyageai
            settings = get_settings()
            self._client = voyageai.Client(api_key=settings.voyage_api_key)

        result = self._client.embed(
            texts=texts,
            model=self.model_name,
            input_type="document",
        )
        return result.embeddings

    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """Embed using OpenAI."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI()

        response = self._client.embeddings.create(
            model=self.model_name,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """Embed using local sentence-transformers model."""
        if self._local_model is None:
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer("all-mpnet-base-v2")

        embeddings = self._local_model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()


@lru_cache
def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service."""
    return EmbeddingService()
