from uuid import UUID

from repositories.conversation.conversation_repository import ConversationRepository
from domain.conversation.value_objects import Query


class AskService:
    def __init__(self, conversation_repository: ConversationRepository) -> None:
        self.repository = conversation_repository

    def execute(self, manuscript_id: UUID, query: str):
        conversation = self.repository.get_by_manuscript_id(manuscript_id)
        conversation.ask(Query(query))

        embedder = Embedder()
        query_vector = embedder.embed(query)

        vector_store = VectorStore()
        chunk_ids: list[ChunkId] = vector_store.search(
            embedding=query_vector,
            top_k=10,
            score_threshold=0.1,
            metadata={"manuscript_id": manuscript_id},
        )

        indexed_document_repository = IndexedDocumentRepository()
        chunks: ScoredChunks = []

        for id in chunk_ids:
            chunks.append(indexed_document_repository.get_by_manuscript_id(id))

        # Relevance policy filters
        #
        # Context Assembler builds prompt

        # LLMClient.complete()

        # Build Answer with PassageRefrences from the Chunks Supplied

        # record_answer save the conversation, return the answer.
