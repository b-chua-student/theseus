from ports.generation.answer_generator import AnswerGenerator


class FakeGenerator(AnswerGenerator):
    def __init__(self, reply: str = "Answer [1].", error: Exception | None = None) -> None:
        self._reply = reply
        self._error = error
        self.calls: list[str] = []

    def generate(self, query, passages, history):  # type: ignore[no-untyped-def]
        self.calls.append(query)
        if self._error:
            raise self._error
        return self._reply
