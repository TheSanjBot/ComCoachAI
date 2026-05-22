from __future__ import annotations

import json
import logging
from typing import Any
from uuid import uuid4

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)


class SemanticMemoryService:
    def __init__(self) -> None:
        settings.chroma_persist_directory_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(settings.chroma_persist_directory_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(name=settings.chroma_collection)
        self._encoder = SentenceTransformer(settings.embedding_model)

    def provider_available(self) -> bool:
        return True

    def retrieve_user_context(
        self,
        user_id: str,
        query_text: str | None = None,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        if not query_text:
            query_text = "recent coaching context"

        embedding = self._encoder.encode(query_text).tolist()
        query_result = self._collection.query(
            query_embeddings=[embedding],
            n_results=limit,
            where={"user_id": str(user_id)},
        )

        documents = (query_result.get("documents") or [[]])[0]
        metadatas = (query_result.get("metadatas") or [[]])[0]
        payloads: list[dict[str, Any]] = []
        for document, metadata in zip(documents, metadatas):
            payloads.append(
                {
                    "summary": document,
                    "metadata": self._decode_metadata(metadata),
                }
            )
        return payloads

    def store_memory(
        self,
        user_id: str,
        summary_text: str,
        metadata: dict[str, Any],
    ) -> None:
        embedding = self._encoder.encode(summary_text).tolist()
        self._collection.add(
            ids=[uuid4().hex],
            documents=[summary_text],
            embeddings=[embedding],
            metadatas=[
                {
                    "user_id": str(user_id),
                    "metadata_json": json.dumps(metadata),
                }
            ],
        )

    @staticmethod
    def _decode_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
        if not metadata:
            return {}
        raw_metadata = metadata.get("metadata_json")
        if not isinstance(raw_metadata, str):
            return {}
        try:
            return json.loads(raw_metadata)
        except json.JSONDecodeError:
            return {}


memory_service = SemanticMemoryService()
