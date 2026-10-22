from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime

import pytest

import tontine.classic as classic
from tontine.classic import ClassicRotation


def test_seeded_rotation_is_reproducible_for_the_same_member_set() -> None:
    occurred_at = datetime(2027, 1, 15, 12, 0, tzinfo=UTC)

    first = ClassicRotation.randomized(
        ("member-c", "member-a", "member-b"),
        seed="meeting-2027-01",
        actor_id="treasurer-1",
        occurred_at=occurred_at,
    )
    repeated = ClassicRotation.randomized(
        ("member-b", "member-c", "member-a"),
        seed="meeting-2027-01",
        actor_id="treasurer-2",
        occurred_at=datetime(2027, 1, 16, tzinfo=UTC),
    )

    assert first.member_ids == repeated.member_ids
    assert first.member_ids == ("member-a", "member-c", "member-b")
    assert first.randomization is not None
    assert first.randomization.algorithm_version == "sha256-fisher-yates-v1"
    assert first.randomization.active_member_ids == (
        "member-a",
        "member-b",
        "member-c",
    )
    assert first.randomization.generated_order == first.member_ids
    assert first.randomization.seed == "meeting-2027-01"
    assert first.randomization.actor_id == "treasurer-1"
    assert first.randomization.occurred_at is occurred_at


def test_recipient_lookups_use_the_recorded_order_without_randomizing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rotation = ClassicRotation.randomized(
        ("member-a", "member-b", "member-c"),
        seed="lookup-test",
        actor_id="treasurer-1",
        occurred_at=datetime(2027, 1, 15, tzinfo=UTC),
    )

    def fail_if_randomized(*args: object, **kwargs: object) -> tuple[str, ...]:
        raise AssertionError("Recipient lookup must not randomize again.")

    monkeypatch.setattr(classic, "_seeded_order", fail_if_randomized)

    recipients = tuple(rotation.recipient_for_cycle(cycle) for cycle in range(1, 4))
    assert recipients == rotation.member_ids
    assert rotation.recipient_for_cycle(4) == rotation.member_ids[0]


def test_rotation_reconstructs_and_verifies_historical_provenance() -> None:
    rotation = ClassicRotation.randomized(
        ("member-a", "member-b", "member-c", "member-d"),
        seed="historical-rotation",
        actor_id="secretary-1",
        occurred_at=datetime(2027, 1, 15, tzinfo=UTC),
    )
    assert rotation.randomization is not None

    restored = ClassicRotation.from_randomization(rotation.randomization)

    assert restored == rotation
    assert restored.randomization is rotation.randomization

    tampered = replace(
        rotation.randomization,
        generated_order=tuple(reversed(rotation.randomization.generated_order)),
    )
    with pytest.raises(ValueError, match="does not match"):
        ClassicRotation.from_randomization(tampered)


def test_randomized_rotation_rejects_invalid_provenance_inputs() -> None:
    arguments = {
        "active_member_ids": ("member-a", "member-b"),
        "seed": "seed-1",
        "actor_id": "treasurer-1",
        "occurred_at": datetime(2027, 1, 15, tzinfo=UTC),
    }

    with pytest.raises(ValueError, match="duplicate"):
        ClassicRotation.randomized(
            ("member-a", "member-a"),
            "seed-1",
            "treasurer-1",
            datetime(2027, 1, 15, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="seed"):
        ClassicRotation.randomized(**{**arguments, "seed": " "})
    with pytest.raises(ValueError, match="actor"):
        ClassicRotation.randomized(**{**arguments, "actor_id": " "})
    with pytest.raises(
        ValueError,
        match=r"occurred_at must be timezone-aware.*datetime\.timezone\.utc",
    ):
        ClassicRotation.randomized(
            **{**arguments, "occurred_at": datetime(2027, 1, 15)}
        )

    rotation = ClassicRotation.randomized(**arguments)
    assert rotation.randomization is not None
    with pytest.raises(FrozenInstanceError):
        rotation.randomization.seed = "changed"
