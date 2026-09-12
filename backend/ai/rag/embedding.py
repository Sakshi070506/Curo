"""
Module   : Embedding Generator
Owner    : ML Engineer
Purpose  : Generates embeddings for clinical knowledge base entries.
"""

import os
from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from backend.ai.common import LLMClient, LLMConfig, MockLLMClient


@dataclass
class EmbeddingConfig:
    provider: str = "local"
    model_name: str = "all-MiniLM-L6-v2"
    api_base_url: str = ""
    api_key: str = ""
    dimension: int = 384

    def __post_init__(self):
        self.provider = os.getenv("EMBEDDING_PROVIDER", self.provider)
        self.model_name = os.getenv("EMBEDDING_MODEL", self.model_name)
        self.api_base_url = os.getenv("EMBEDDING_API_URL", self.api_base_url)
        self.api_key = os.getenv("EMBEDDING_API_KEY", self.api_key)


class EmbeddingModel:
    """Provider-agnostic embedding model."""

    def __init__(self, config: EmbeddingConfig | None = None):
        self.config = config or EmbeddingConfig()
        self._model = None
        self._client = None

        if self.config.provider == "local":
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise RuntimeError("sentence-transformers not installed. Run: pip install sentence-transformers")
            self._model = SentenceTransformer(self.config.model_name)
            self.config.dimension = self._model.get_sentence_embedding_dimension()
        else:
            llm_config = LLMConfig(
                provider=self.config.provider,
                base_url=self.config.api_base_url,
                api_key=self.config.api_key,
                model=self.config.model_name,
            )
            self._client = LLMClient(llm_config)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        if self.config.provider == "local":
            return self._embed_local(texts)
        else:
            return self._embed_api(texts)

    def _embed_local(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()

    async def _embed_api_async(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        for text in texts:
            resp = await self._client.chat(
                [{"role": "user", "content": f"Embed: {text}"}],
                task="embedding",
            )
            parsed = resp if isinstance(resp, list) else []
            embeddings.append(parsed)
        return embeddings

    def _embed_api(self, texts: list[str]) -> list[list[float]]:
        import asyncio
        return asyncio.run(self._embed_api_async(texts))

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query text."""
        return self.embed_texts([query])[0]

    def embed_concept(self, concept: dict[str, Any]) -> list[float]:
        """Embed a clinical concept (name + description)."""
        text = f"{concept.get('name', '')} {concept.get('description', '')}".strip()
        return self.embed_query(text)


class MockEmbeddingModel:
    """Deterministic mock embeddings for testing."""

    def __init__(self, config: EmbeddingConfig | None = None):
        self.config = config or EmbeddingConfig()
        self.config.dimension = 384

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        import hashlib
        results = []
        for text in texts:
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            np.random.seed(hash_val % (2**32))
            vec = np.random.normal(0, 1, self.config.dimension)
            vec = vec / np.linalg.norm(vec)
            results.append(vec.tolist())
        return results

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]

    def embed_concept(self, concept: dict[str, Any]) -> list[float]:
        text = f"{concept.get('name', '')} {concept.get('description', '')}".strip()
        return self.embed_query(text)


def get_embedding_model(config: EmbeddingConfig | None = None):
    """Factory function to get embedding model."""
    cfg = config or EmbeddingConfig()
    if cfg.provider == "mock":
        return MockEmbeddingModel(cfg)
    return EmbeddingModel(cfg)


__all__ = [
    "EmbeddingConfig",
    "EmbeddingModel",
    "MockEmbeddingModel",
    "get_embedding_model",
]