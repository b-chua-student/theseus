import pytest
from domain.conversation.aggregates import Conversation, InvalidManuscriptId


def test_invalid_manuscript_id_raises_error():
    with pytest.raises(InvalidManuscriptId):
        Conversation.create(1111111)
