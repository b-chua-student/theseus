from uuid import UUID

from pymongo.database import Database

from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.aggregates import MAIN, RevisionHistory
from domain.revision_history.models.entities import Branch, Revision
from domain.revision_history.models.value_objects import (
    ManuscriptId,
    RevisionId,
    SectionSnapshot,
    Snapshot,
)


class MongoRevisionHistoryRepository(RevisionHistoryRepository):
    """Revision history split across two collections.

    ``revision_histories`` holds one document per manuscript: the current draft
    and, for each draft, the *ordered ids* of its revisions. ``revisions`` holds
    each revision (with its full snapshot) exactly once.

    Splitting them matters because a revision can belong to several drafts
    (creating a draft copies the revisions of ``main``) and every revision carries
    a full manuscript snapshot. Embedding revisions per draft would duplicate
    every snapshot into every draft and grow toward MongoDB's 16MB document limit.
    Drafts are stored as a list, not keyed by name, because draft names are
    user-supplied and may contain characters that are invalid in field names.
    """

    def __init__(
        self,
        database: Database,
        *,
        histories: str = "revision_histories",
        revisions: str = "revisions",
    ) -> None:
        self._histories = database[histories]
        self._revisions = database[revisions]
        self._revisions.create_index("manuscript_id")

    # ---- mapping ----
    @staticmethod
    def _revision_to_doc(manuscript_key: str, revision: Revision) -> dict:
        return {
            "_id": str(revision.id.value),
            "manuscript_id": manuscript_key,
            "message": revision.message,
            "created_at": revision.created_at,
            "snapshot": [
                {
                    "id": str(s.id),
                    "parent_id": str(s.parent_id) if s.parent_id else None,
                    "heading": s.heading,
                    "ordinal": s.ordinal,
                    "body": s.body,
                }
                for s in revision.snapshot.sections
            ],
        }

    @staticmethod
    def _revision_from_doc(doc: dict) -> Revision:
        return Revision(
            id=RevisionId(UUID(doc["_id"])),
            message=doc["message"],
            created_at=doc["created_at"],
            snapshot=Snapshot(
                tuple(
                    SectionSnapshot(
                        id=UUID(s["id"]),
                        parent_id=UUID(s["parent_id"]) if s["parent_id"] else None,
                        heading=s["heading"],
                        ordinal=s["ordinal"],
                        body=s["body"],
                    )
                    for s in doc["snapshot"]
                )
            ),
        )

    # ---- port implementation ----
    def get_by_manuscript_id(self, manuscript_id: ManuscriptId) -> RevisionHistory | None:
        doc = self._histories.find_one({"_id": str(manuscript_id.value)})
        if doc is None:
            return None

        wanted = {rid for branch in doc["drafts"] for rid in branch["revisions"]}
        revisions = {
            d["_id"]: self._revision_from_doc(d)
            for d in self._revisions.find({"_id": {"$in": list(wanted)}})
        }
        missing = wanted - revisions.keys()
        if missing:
            raise LookupError(
                f"Revision history for {manuscript_id.value} references missing revisions: "
                f"{sorted(missing)}"
            )

        branches = {
            d["name"]: Branch(d["name"], [revisions[rid] for rid in d["revisions"]])
            for d in doc["drafts"]
        }
        return RevisionHistory.rehydrate(manuscript_id, branches, doc.get("current", MAIN))

    def add(self, history: RevisionHistory) -> None:
        self.save(history)

    def save(self, history: RevisionHistory) -> None:
        key = str(history.manuscript_id.value)
        branches = history.branches
        referenced = {str(r.id.value): r for b in branches for r in b.revisions}

        # Write order keeps the data consistent if we fail midway: revisions first
        # (harmless if the history doc is never updated), then the history doc that
        # points at them, then clean-up of revisions no draft references any more.
        stored = {d["_id"] for d in self._revisions.find({"manuscript_id": key}, {"_id": 1})}
        fresh = [
            self._revision_to_doc(key, r) for rid, r in referenced.items() if rid not in stored
        ]
        if fresh:
            self._revisions.insert_many(fresh)

        self._histories.replace_one(
            {"_id": key},
            {
                "_id": key,
                "current": history.current_draft.name,
                "drafts": [
                    {"name": b.name, "revisions": [str(r.id.value) for r in b.revisions]}
                    for b in branches
                ],
            },
            upsert=True,
        )

        orphaned = stored - referenced.keys()
        if orphaned:
            self._revisions.delete_many({"_id": {"$in": list(orphaned)}})
