"""Route the combined-context Gherkin scenarios by tag.

``@service`` and ``@acceptance`` scenarios run here. ``@component`` scenarios are bound in
Vitest (``frontend/src/components/chat/combinedContext.scenarios.spec.js``), so they are
deselected from pytest. Other tags (``@S-###``, ``@criterion-#``) are traceability labels and
are not turned into pytest markers.
"""

from collections.abc import Callable

import pytest

FRONTEND_ONLY = "frontend_scenario"


def pytest_configure(config: pytest.Config) -> None:
    """Register the marker used to deselect component scenarios."""
    config.addinivalue_line("markers", f"{FRONTEND_ONLY}: Gherkin scenario bound in Vitest")


def pytest_bdd_apply_tag(tag: str, function: Callable[..., object]) -> bool:
    """Mark component scenarios for deselection and ignore the other tags."""
    if tag == "component":
        getattr(pytest.mark, FRONTEND_ONLY)(function)
    return True


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Deselect the scenarios that run in Vitest."""
    selected = [item for item in items if item.get_closest_marker(FRONTEND_ONLY) is None]
    deselected = [item for item in items if item.get_closest_marker(FRONTEND_ONLY) is not None]
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected
