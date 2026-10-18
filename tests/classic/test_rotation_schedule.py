from datetime import UTC, datetime
from decimal import Decimal

import pytest

from tontine.classic import (
    ApprovedRotationException,
    ClassicRotation,
    ClassicRotationSchedule,
    ClassicRotationVersion,
    UnpaidContributionPolicy,
    can_pay_out,
)
from tontine.exceptions import MissingRecordError


def rotation(*member_ids: str) -> ClassicRotation:
    return ClassicRotation.from_active_members(member_ids)


def version(
    number: int,
    effective_cycle: int,
    *member_ids: str,
) -> ClassicRotationVersion:
    return ClassicRotationVersion(
        version=number,
        effective_cycle=effective_cycle,
        rotation=rotation(*member_ids),
        source_event=f"rotation-approved-{number}",
    )


def approved_exception(
    cycle_number: int,
    recipient_id: str,
    exception_id: str = "exception-1",
) -> ApprovedRotationException:
    return ApprovedRotationException(
        exception_id=exception_id,
        cycle_number=cycle_number,
        recipient_id=recipient_id,
        proposal_id=f"proposal-{exception_id}",
        approval_event_id=f"approval-{exception_id}",
        approved_at=datetime(2027, 1, 15, tzinfo=UTC),
    )


def test_schedule_resolves_latest_effective_rotation_version() -> None:
    initial = version(1, 1, "member-a", "member-b", "member-c")
    later = version(2, 4, "member-c", "member-b", "member-a")
    schedule = ClassicRotationSchedule((later, initial))

    assert schedule.version_for_cycle(1) is initial
    assert schedule.version_for_cycle(3) is initial
    assert schedule.version_for_cycle(4) is later
    assert schedule.resolve_cycle(4).recipient_id == "member-c"


def test_equal_effective_cycle_tiebreaker_is_immutable() -> None:
    initial = version(1, 1, "member-a", "member-b", "member-c")
    schedule = ClassicRotationSchedule((initial,))
    revised = schedule.with_version(version(2, 1, "member-c", "member-b", "member-a"))

    assert schedule.version_for_cycle(1) is initial
    assert revised.version_for_cycle(1).version == 2
    assert revised.resolve_cycle(1).recipient_id == "member-c"


def test_later_version_does_not_change_historical_cycle_resolution() -> None:
    initial = version(1, 1, "member-a", "member-b", "member-c")
    schedule = ClassicRotationSchedule((initial,))
    revised = schedule.with_version(version(2, 4, "member-c", "member-b", "member-a"))

    assert revised.version_for_cycle(3) is initial
    assert revised.version_for_cycle(4).version == 2
    assert schedule.versions == (initial,)


def test_approved_exception_overrides_only_its_cycle_recipient() -> None:
    initial = version(1, 1, "member-a", "member-b", "member-c")
    schedule = ClassicRotationSchedule((initial,))
    exception = approved_exception(cycle_number=2, recipient_id="member-a")
    revised = schedule.with_exception(exception)

    assert revised.resolve_cycle(1).recipient_id == "member-a"
    at_exception = revised.resolve_cycle(2)
    assert at_exception.recipient_id == "member-a"
    assert at_exception.exception is exception
    assert at_exception.rotation_version is initial
    assert revised.resolve_cycle(3).recipient_id == "member-c"
    assert schedule.resolve_cycle(2).recipient_id == "member-b"


def test_exception_does_not_change_payout_or_unpaid_policy() -> None:
    initial = version(1, 1, "member-a", "member-b", "member-c")
    schedule = ClassicRotationSchedule((initial,)).with_exception(
        approved_exception(cycle_number=2, recipient_id="member-a")
    )
    resolved = schedule.resolve_cycle(2)
    contributions = {
        "member-a": Decimal("10"),
        "member-b": Decimal("20"),
        "member-c": Decimal("30"),
    }

    assert resolved.recipient_id == "member-a"
    assert resolved.rotation_version.rotation.expected_payout(contributions) == (
        Decimal("60")
    )
    assert can_pay_out(Decimal("1"), UnpaidContributionPolicy.DENY) is False


def test_schedule_rejects_missing_versions_invalid_cycles_and_duplicates() -> None:
    with pytest.raises(ValueError, match="at least one"):
        ClassicRotationSchedule(())
    with pytest.raises(MissingRecordError, match="No rotation version"):
        ClassicRotationSchedule((version(1, 2, "member-a"),)).version_for_cycle(1)
    with pytest.raises(ValueError, match="positive"):
        ClassicRotationSchedule((version(1, 1, "member-a"),)).version_for_cycle(0)

    schedule = ClassicRotationSchedule((version(1, 1, "member-a"),))
    with pytest.raises(ValueError, match="already exists"):
        schedule.with_version(version(1, 2, "member-a"))
    with pytest.raises(ValueError, match="unique"):
        ClassicRotationSchedule((version(1, 1, "member-a"),) * 2)


def test_schedule_rejects_invalid_exception_scope_and_recipient() -> None:
    schedule = ClassicRotationSchedule(
        (version(1, 1, "member-a", "member-b"),)
    )
    with pytest.raises(ValueError, match="effective rotation"):
        schedule.with_exception(approved_exception(2, "member-x"))

    exception = approved_exception(2, "member-a")
    schedule_with_exception = schedule.with_exception(exception)
    with pytest.raises(ValueError, match="already has a rotation exception"):
        schedule_with_exception.with_exception(
            approved_exception(2, "member-b", exception_id="exception-2")
        )
    with pytest.raises(ValueError, match="positive"):
        approved_exception(0, "member-a")
    with pytest.raises(MissingRecordError, match="No rotation version"):
        ClassicRotationSchedule((version(1, 2, "member-a"),)).with_exception(
            approved_exception(1, "member-a")
        )


def test_rotation_version_and_exception_validate_provenance() -> None:
    with pytest.raises(ValueError, match="positive"):
        version(0, 1, "member-a")
    with pytest.raises(ValueError, match="source event"):
        ClassicRotationVersion(1, 1, rotation("member-a"), " ")
    with pytest.raises(ValueError, match="approval event"):
        ApprovedRotationException(
            exception_id="exception-1",
            cycle_number=1,
            recipient_id="member-a",
            proposal_id="proposal-1",
            approval_event_id=" ",
            approved_at=datetime(2027, 1, 15, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match=r"approved_at must be timezone-aware.*datetime\.timezone\.utc",
    ):
        ApprovedRotationException(
            exception_id="exception-1",
            cycle_number=1,
            recipient_id="member-a",
            proposal_id="proposal-1",
            approval_event_id="approval-1",
            approved_at=datetime(2027, 1, 15),
        )
