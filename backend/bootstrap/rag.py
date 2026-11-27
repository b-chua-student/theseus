"""Resolve the pinned MiniLM snapshot. Run this module to provision it before startup."""

from pathlib import Path

from huggingface_hub import snapshot_download

MINILM_REPO = "sentence-transformers/all-MiniLM-L6-v2"
MINILM_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
MINILM_FILES = ("tokenizer.json", "onnx/model.onnx")


def minilm_snapshot(*, local_files_only: bool = True) -> Path:
    """Return a complete local snapshot, downloading only during explicit provisioning."""
    path = Path(
        snapshot_download(
            MINILM_REPO,
            revision=MINILM_REVISION,
            allow_patterns=list(MINILM_FILES),
            local_files_only=local_files_only,
        )
    )
    for name in MINILM_FILES:
        if not (path / name).is_file():
            raise FileNotFoundError(f"MiniLM snapshot is missing {name} in {path}")
    return path


if __name__ == "__main__":
    minilm_snapshot(local_files_only=False)
