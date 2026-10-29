from uuid import UUID

from domain.conversation.value_objects import Answer, PassageReference, Query
from ports.generation.answer_generator import AnswerGenerator
from ports.retrieval.retriever import Retriever
from repositories.conversation.conversation_repository import ConversationRepository
from domain.conversation.aggregates import Conversation
from domain.conversation.entities import Exchange


class AskQuestionService:
    def __init__(
        self,
        repository: ConversationRepository,
        retriever: Retriever,
        generator: AnswerGenerator,
        top_k: int = 5,
        history_limit: int = 6,
    ) -> None:
        self._repository = repository
        self._retriever = retriever
        self._generator = generator
        self._top_k = top_k
        self._history_limit = history_limit

    def execute(self, manuscript_id: UUID, content: str) -> Exchange:
        conversation = self._repository.get_by_manuscript_id(manuscript_id)
        if conversation is None:
            conversation = Conversation.create(manuscript_id)

        history = conversation.history(self._history_limit)
        exchange = conversation.ask(content)
        self._repository.save(conversation)

        passages = self._retriever.retrieve(manuscript_id, content, self._top_k)
        text = self._generator.generate(content, passages, history)

        answer = Answer(
            content=text,
            sources=tuple(
                PassageReference(p.chunk_id, p.section_id, p.text[:200], p.score)
                for p in passages
            ),
        )
        recorded = conversation.record_answer(exchange.id, answer)
        self._repository.save(conversation)
        return recorded
