"""Unit tests for the in-process event bus."""

from dataclasses import dataclass

from domain.src_lib.infrastructure.adapters.in_process_event_bus import (
    InProcessEventBus,
)


@dataclass
class SampleEvent:
    """Sample event used for testing."""

    message: str


@dataclass
class OtherEvent:
    """Different event type used for testing."""

    message: str


def test_publish_dispatches_event() -> None:
    """Deliver an event to its subscribed handler."""
    bus = InProcessEventBus()
    received: list[SampleEvent] = []
    event = SampleEvent("created")

    bus.subscribe(SampleEvent, received.append)
    bus.publish([event])

    assert received == [event]


def test_publish_without_subscribers() -> None:
    """Allow publishing without registered handlers."""
    bus = InProcessEventBus()

    bus.publish([SampleEvent("created")])


def test_multiple_subscribers() -> None:
    """Deliver an event to every registered handler."""
    bus = InProcessEventBus()
    first: list[SampleEvent] = []
    second: list[SampleEvent] = []
    event = SampleEvent("updated")

    bus.subscribe(SampleEvent, first.append)
    bus.subscribe(SampleEvent, second.append)
    bus.publish([event])

    assert first == [event]
    assert second == [event]


def test_dispatch_only_matching_event_type() -> None:
    """Deliver events only to matching subscribers."""
    bus = InProcessEventBus()
    received: list[SampleEvent] = []

    bus.subscribe(SampleEvent, received.append)
    bus.publish([OtherEvent("ignored")])

    assert received == []


def test_publish_multiple_events_in_order() -> None:
    """Preserve the order of published events."""
    bus = InProcessEventBus()
    received: list[SampleEvent] = []
    events = [
        SampleEvent("created"),
        SampleEvent("updated"),
        SampleEvent("removed"),
    ]

    bus.subscribe(SampleEvent, received.append)
    bus.publish(events)

    assert received == events


def test_handler_failure_does_not_stop_dispatch() -> None:
    """Continue dispatching when another handler fails."""
    bus = InProcessEventBus()
    received: list[SampleEvent] = []
    event = SampleEvent("created")

    def failing_handler(event: SampleEvent) -> None:
        raise RuntimeError(event.message)

    bus.subscribe(SampleEvent, failing_handler)
    bus.subscribe(SampleEvent, received.append)
    bus.publish([event])

    assert received == [event]


def test_publish_empty_events() -> None:
    """Do not call handlers for an empty event batch."""
    bus = InProcessEventBus()
    received: list[SampleEvent] = []

    bus.subscribe(SampleEvent, received.append)
    bus.publish([])

    assert received == []
