from unittest.mock import MagicMock

from pymongo.database import Database

from domain.manuscript.infrastructure.adapters.mongodb_manuscript_repository import (
    MongoManuscriptRepository,
)
from domain.manuscript.models.aggregates import Manuscript
from domain.manuscript.models.value_objects import Heading, ManuscriptTitle, ProjectId


def test_mongo_round_trip_preserves_nested_sections_and_scopes_project_query() -> None:
    database = MagicMock(spec=Database)
    collection = database.__getitem__.return_value
    repository = MongoManuscriptRepository(database)
    manuscript = Manuscript.create(ProjectId.new(), ManuscriptTitle("Thesis"), template=False)
    manuscript.append_section(None, Heading("Methods"))
    parent = manuscript.sections[0]
    manuscript.append_section(parent.id, Heading("Sampling"))
    child = manuscript.sections[1]
    manuscript.edit_section_body(child.id, "Sampling details")

    repository.save(manuscript)

    selector, update = collection.update_one.call_args.args
    assert selector == {"_id": str(manuscript.id.value)}
    assert collection.update_one.call_args.kwargs == {"upsert": True}
    fields = update["$set"]
    assert fields["sections"] == [
        {
            "id": str(parent.id.value),
            "parent_id": None,
            "heading": "Methods",
            "ordinal": 1,
            "body": "",
        },
        {
            "id": str(child.id.value),
            "parent_id": str(parent.id.value),
            "heading": "Sampling",
            "ordinal": 2,
            "body": "Sampling details",
        },
    ]
    collection.find.return_value.sort.return_value = [{**selector, **fields}]

    [loaded] = repository.list_by_project_id(manuscript.project_id)

    collection.find.assert_called_once_with({"project_id": str(manuscript.project_id.value)})
    collection.find.return_value.sort.assert_called_once_with("created_at", 1)
    assert loaded.id == manuscript.id
    assert loaded.project_id == manuscript.project_id
    assert loaded.title == manuscript.title
    assert [section.id for section in loaded.sections] == [parent.id, child.id]
    assert loaded.sections[1].parent_id == loaded.sections[0].id
    assert loaded.sections[1].body == "Sampling details"
