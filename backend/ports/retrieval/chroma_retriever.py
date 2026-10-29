from uuid import UUID

from chromadb.api.models.Collection import Collection

from ports.embedding.embedder import Embedder
from ports.retrieval.retriever import RetrievedPassage, Retriever


class ChromaRetriever(Retriever):
    def __init__(self, collection: Collection, embedder: Embedder) -> None:
        self._collection = collection
        self._embedder = embedder

    def retrieve(self, manuscript_id: UUID, query: str, limit: int) -> list[RetrievedPassage]:
        vector = self._embedder.embed([query])[0]

        result = self._collection.query(
            query_embeddings=[vector],
            n_results=limit,
            where={
                "$and": [
                    {"owner_id": str(manuscript_id)},
                    {"model_name": self._embedder.model.name},
                ]
            },
            include=["documents", "metadatas", "distances"],
        )

        ids = (result["ids"] or [[]])[0]
        documents = (result["documents"] or [[]])[0]
        metadatas = (result["metadatas"] or [[]])[0]
        distances = (result["distances"] or [[]])[0]

        return [
            RetrievedPassage(
                chunk_id=UUID(chunk_id),
                section_id=UUID(str(meta["section_id"])),
                text=text,
                score=1.0 - distance,
            )
            for chunk_id, text, meta, distance in zip(ids, documents, metadatas, distances)
        ]
