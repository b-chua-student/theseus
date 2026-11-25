"""Publish elapsed intervals between successful production deployments."""

import os
import re
import sys
from datetime import timedelta
from itertools import pairwise
from pathlib import Path

from scripts.dora_evidence import EvidenceError, fetch_production_arrivals

TITLE = "DORA deployment frequency"


def format_interval(interval: timedelta) -> str:
    """Render an exact duration in days, hours, minutes, and seconds."""
    hours, remainder = divmod(interval.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = [
        f"{count} {unit}{'' if count == 1 else 's'}"
        for count, unit in ((interval.days, "day"), (hours, "hour"), (minutes, "minute"))
        if count
    ]
    if interval.microseconds:
        parts.append(f"{seconds}.{interval.microseconds:06d}".rstrip("0") + " seconds")
    elif seconds:
        parts.append(f"{seconds} {'second' if seconds == 1 else 'seconds'}")
    return ", ".join(parts) if parts else "0 seconds"


def main() -> int:
    """Validate deployment evidence and write the GitHub Actions job summary."""
    try:
        service = os.environ["DORA_RENDER_SERVICE_ID"]
        token = os.environ["RENDER_API_KEY"]
        first_id = os.environ["DORA_RENDER_FIRST_DEPLOY_ID"]
        summary = Path(os.environ["GITHUB_STEP_SUMMARY"])
        if not (
            re.fullmatch(r"srv-[A-Za-z0-9]+", service)
            and re.fullmatch(r"(?:dep-[A-Za-z0-9]+|empty)", first_id)
            and token.strip()
        ):
            raise EvidenceError("Required reporting configuration is missing or invalid.")

        arrivals = sorted(live for _, live in fetch_production_arrivals(service, token, first_id))
        lines = [f"## {TITLE}", "", f"Successful production deployments: {len(arrivals)}", ""]
        if len(arrivals) < 2:
            lines.append(
                "Deployment interval unavailable. At least two deployments must reach production."
            )
        else:
            lines.extend(
                f"- {format_interval(later - earlier)}" for earlier, later in pairwise(arrivals)
            )
        summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except EvidenceError as error:
        sys.stderr.write(f"{error}\n")
        return 1
    except KeyError:
        sys.stderr.write("Required reporting configuration is missing.\n")
        return 1
    except OSError:
        sys.stderr.write("Unable to write the deployment frequency summary.\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
