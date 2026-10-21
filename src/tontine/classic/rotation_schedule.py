"""Effective-cycle classic rotation versions and recipient exceptions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import TYPE_CHECKING

from tontine._datetime import require_aware_datetime
from tontine.exceptions import MissingRecordError

if TYPE_CHECKING:
    from tontine.members import ParticipationShareRegistry

    from . import ClassicRotation


@dataclass(frozen=True)
class ClassicRotationVersion:
    """Immutable rotation order effective from a one-based cycle."""

    version: int
    effective_cycle: int
    rotation: ClassicRotation
    source_event: str

    def __post_init__(self) -> None:
        from . import ClassicRotation

        if self.version < 1 or self.effective_cycle < 1:
            raise ValueError("Rotation version and effective cycle must be positive.")
        if not self.source_event.strip():
            raise ValueError("Rotation version source event is required.")
        if not isinstance(self.rotation, ClassicRotation):
            raise TypeError("Rotation versions require a ClassicRotation.")
        ClassicRotation.from_active_members(self.rotation.member_ids)


@dataclass(frozen=True)
class ApprovedRotationException:
    """Auditable approval effect overriding one cycle's recipient only.

    Payout calculation and unpaid-contribution eligibility continue to use the
    existing classic rules; the exception does not modify the base rotation.
    """

    exception_id: str
    cycle_number: int
    recipient_id: str
    proposal_id: str
    approval_event_id: str
    approved_at: datetime

    def __post_init__(self) -> None:
        if not self.exception_id.strip():
            raise ValueError("Rotation exception identifier is required.")
        if self.cycle_number < 1:
            raise ValueError("Rotation exception cycle must be positive.")
        if not self.recipient_id.strip():
            raise ValueError("Rotation exception recipient is required.")
        if not self.proposal_id.strip():
            raise ValueError("Rotation exception proposal identifier is required.")
        if not self.approval_event_id.strip():
            raise ValueError("Rotation exception approval event is required.")
        require_aware_datetime(self.approved_at, "approved_at")


@dataclass(frozen=True)
class ClassicRotationResolution:
    """Resolved base version and the recipient selected for one cycle."""

    cycle_number: int
    rotation_version: ClassicRotationVersion
    recipient_id: str
    exception: ApprovedRotationException | None


@dataclass(frozen=True)
class ClassicRotationSchedule:
    """Immutable schedule resolving rotation versions and approved exceptions.

    The applicable version is the one with the latest effective cycle. If more
    than one version shares that cycle, the highest version number wins.
    """

    versions: tuple[ClassicRotationVersion, ...]
    exceptions: tuple[ApprovedRotationException, ...] = ()

    def __post_init__(self) -> None:
        versions = tuple(self.versions)
        exceptions = tuple(self.exceptions)
        if not versions:
            raise ValueError("A rotation schedule requires at least one version.")
        if any(not isinstance(item, ClassicRotationVersion) for item in versions):
            raise TypeError("Rotation schedules require ClassicRotationVersion values.")
        if len({item.version for item in versions}) != len(versions):
            raise ValueError("Rotation version numbers must be unique.")
        versions = tuple(
            sorted(versions, key=lambda item: (item.effective_cycle, item.version))
        )
        if any(not isinstance(item, ApprovedRotationException) for item in exceptions):
            raise TypeError(
                "Rotation schedules require ApprovedRotationException values."
            )
        if len({item.exception_id for item in exceptions}) != len(exceptions):
            raise ValueError("Rotation exception identifiers must be unique.")
        if len({item.cycle_number for item in exceptions}) != len(exceptions):
            raise ValueError(
                "Only one approved rotation exception is allowed per cycle."
            )
        exceptions = tuple(sorted(exceptions, key=lambda item: item.cycle_number))
        object.__setattr__(self, "versions", versions)
        object.__setattr__(self, "exceptions", exceptions)

        for exception in exceptions:
            rotation = self.version_for_cycle(exception.cycle_number).rotation
            if exception.recipient_id not in rotation.member_ids:
                raise ValueError(
                    "Rotation exception recipient must belong to the effective "
                    "rotation."
                )

    def with_version(
        self,
        version: ClassicRotationVersion,
    ) -> ClassicRotationSchedule:
        """Return a schedule with an additional immutable rotation version.

        A higher version number takes precedence when effective cycles match.

        Raises:
            ValueError: If the version number is already present.
        """
        if not isinstance(version, ClassicRotationVersion):
            raise TypeError("Expected a ClassicRotationVersion.")
        if any(item.version == version.version for item in self.versions):
            raise ValueError(f"Rotation version {version.version} already exists.")
        return replace(self, versions=(*self.versions, version))

    def with_exception(
        self,
        exception: ApprovedRotationException,
    ) -> ClassicRotationSchedule:
        """Return a schedule with one approved recipient override.

        Raises:
            ValueError: If that cycle already has an exception or the recipient
                is not in the effective rotation.
            MissingRecordError: If no rotation version applies to the cycle.
        """
        if not isinstance(exception, ApprovedRotationException):
            raise TypeError("Expected an ApprovedRotationException.")
        if any(item.cycle_number == exception.cycle_number for item in self.exceptions):
            raise ValueError(
                f"Cycle {exception.cycle_number} already has a rotation exception."
            )
        return replace(self, exceptions=(*self.exceptions, exception))

    def version_for_cycle(self, cycle_number: int) -> ClassicRotationVersion:
        """Return the latest rotation version effective for a cycle.

        Raises:
            ValueError: If ``cycle_number`` is not positive.
            MissingRecordError: If no rotation version applies.
        """
        if cycle_number < 1:
            raise ValueError("Rotation cycle number must be positive.")
        applicable = [
            item for item in self.versions if item.effective_cycle <= cycle_number
        ]
        if not applicable:
            raise MissingRecordError(
                f"No rotation version is effective for cycle {cycle_number}."
            )
        return max(
            applicable,
            key=lambda item: (item.effective_cycle, item.version),
        )

    def resolve_cycle(self, cycle_number: int) -> ClassicRotationResolution:
        """Resolve the base rotation version and recipient for a cycle.

        An approved exception replaces only the recipient for its cycle. The
        returned base rotation remains available for payout calculation.

        Args:
            cycle_number: Positive one-based cycle number.

        Returns:
            The effective rotation version, selected recipient, and any
            applicable exception.
        """
        version = self.version_for_cycle(cycle_number)
        exception = next(
            (item for item in self.exceptions if item.cycle_number == cycle_number),
            None,
        )
        recipient_id = (
            exception.recipient_id
            if exception is not None
            else version.rotation.recipient_for_cycle(cycle_number)
        )
        return ClassicRotationResolution(
            cycle_number=cycle_number,
            rotation_version=version,
            recipient_id=recipient_id,
            exception=exception,
        )

    def resolve_member_for_cycle(
        self,
        cycle_number: int,
        share_registry: ParticipationShareRegistry,
    ) -> str:
        """Resolve a cycle's rotation recipient to the owning person.

        The stored rotation and any approved exception continue to reference
        stable share IDs; this method returns their owner for member-level
        payout and reporting boundaries.

        Args:
            cycle_number: Positive cycle to resolve.
            share_registry: Registry containing the effective share ownership.

        Returns:
            Owning member identifier for the selected share.

        Raises:
            MissingRecordError: If no rotation is effective for the cycle.
            KeyError: If the selected share is not registered.
            ValueError: If the selected share is inactive for the cycle.
        """
        resolution = self.resolve_cycle(cycle_number)
        return str(
            share_registry.member_for_share(
                resolution.recipient_id,
                cycle_number,
            )
        )
