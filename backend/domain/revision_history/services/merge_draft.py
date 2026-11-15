import logging
from contextlib import contextmanager
from threading import Lock

from domain.revision_history.models.errors import (
    InvalidResolutionError,
    MergeInProgressError,
    RevisionError,
    UnsavedChangesError,
)
from domain.revision_history.models.merge import detect_conflicts
from domain.revision_history.models.value_objects import ManuscriptId

from .errors import HistoryNotFound, ManuscriptNotFound

logger = logging.getLogger(__name__)


class MergeLocks:
    def __init__(self):
        self._guard = Lock()
        self._locks = {}

    @contextmanager
    def try_acquire(self, key):
        with self._guard:
            lock = self._locks.setdefault(key, Lock())
        if not lock.acquire(blocking=False):
            raise MergeInProgressError("A merge is already in progress.")
        try:
            yield
        finally:
            lock.release()


class MergeDraftService:
    def __init__(self, repository, reader, writer, locks):
        self._repository = repository
        self._reader = reader
        self._writer = writer
        self._locks = locks

    def execute(self, manuscript_id, source, resolutions=(), message=None):
        valid_id = ManuscriptId.from_str(manuscript_id)
        key = str(valid_id.value)
        with self._locks.try_acquire(key):
            history = self._repository.get_by_manuscript_id(valid_id)
            if history is None:
                raise HistoryNotFound(key)
            working = self._reader.get_snapshot(key)
            if working is None:
                raise ManuscriptNotFound(key)
            if message is not None and not 1 <= len(message) <= 256:
                raise RevisionError("Merge message must contain 1 to 256 characters.")
            target = history.current_draft
            if sorted(working.sections, key=lambda s: s.id) != sorted(
                target.head.snapshot.sections, key=lambda s: s.id
            ):
                raise UnsavedChangesError("Save your changes before merging.")
            source_branch = history.get_branch(source)
            if source == target.name:
                raise RevisionError("A draft cannot be merged into itself.")
            base = history.find_merge_base(target.name, source)
            conflicts = detect_conflicts(
                base.snapshot, target.head.snapshot, source_branch.head.snapshot
            )
            allowed = {(c.section_id, c.field) for c in conflicts}
            seen = set()
            for resolution in resolutions:
                pair = resolution.section_id, resolution.field
                if (
                    pair in seen
                    or pair not in allowed
                    or resolution.choice not in ("target", "source")
                ):
                    raise InvalidResolutionError(
                        "duplicate" if pair in seen else "unmatched", *pair
                    )
                seen.add(pair)
            revision = history.plan_merge(target.name, source, resolutions, message)
            self._writer.apply_snapshot(key, revision.snapshot)
            history.attach(target.name, revision)
            try:
                self._repository.save(history)
            except Exception:
                target.revisions.remove(revision)
                try:
                    self._writer.apply_snapshot(key, working)
                except Exception:
                    logger.exception("Failed to restore working copy after merge save failure")
                raise
            return target
