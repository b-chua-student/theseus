from uuid import UUID

from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.aggregates import MAIN, RevisionHistory
from domain.revision_history.models.entities import Branch, Revision
from domain.revision_history.models.errors import ConcurrentModificationError
from domain.revision_history.models.value_objects import (
    ManuscriptId,
    MergeSource,
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
        """Bind the collections and index revisions by manuscript ID."""
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
            "merged_from": {
                "draft": revision.merged_from.draft_name,
                "head_revision_id": str(revision.merged_from.head_revision_id.value),
            }
            if revision.merged_from
            else None,
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
            merged_from=MergeSource(
                doc["merged_from"]["draft"],
                RevisionId.from_str(doc["merged_from"]["head_revision_id"]),
            )
            if doc.get("merged_from")
            else None,
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
        """Rebuild the stored history and its drafts if the manuscript has one."""
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
        return RevisionHistory.rehydrate(
            manuscript_id, branches, doc.get("current", MAIN), doc.get("version", 0)
        )

    def add(self, history: RevisionHistory) -> None:
        """Persist a new history."""
        self.save(history)

    def save(self, history: RevisionHistory) -> None:
        """Persist the history if its version matches and remove orphaned revisions."""
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

        query = {"_id": key, "version": history.version}
        if history.version == 0:
            query = {"_id": key, "$or": [{"version": 0}, {"version": {"$exists": False}}]}
        try:
            result = self._histories.replace_one(
                query,
                {
                    "_id": key,
                    "version": history.version + 1,
                    "current": history.current_draft.name,
                    "drafts": [
                        {"name": b.name, "revisions": [str(r.id.value) for r in b.revisions]}
                        for b in branches
                    ],
                },
                upsert=history.version == 0,
            )
        except DuplicateKeyError as error:
            raise ConcurrentModificationError("History changed during the operation.") from error
        if not result.matched_count and result.upserted_id is None:
            raise ConcurrentModificationError("History changed during the operation.")
        history.version += 1

        orphaned = stored - referenced.keys()
        if orphaned:
            self._revisions.delete_many({"_id": {"$in": list(orphaned)}})
