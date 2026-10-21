"""Responsibility assignments and configurable conflict findings."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import combinations

from .identity import MemberId


def _required_name(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} is required.")
    return normalized


@dataclass(frozen=True, slots=True)
class ResponsibilityAssignment:
    """Assign one named responsibility to a member within a scope."""

    assignment_id: str
    member_id: str
    responsibility: str
    scope_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "assignment_id", _required_name(self.assignment_id, "Assignment ID")
        )
        object.__setattr__(self, "member_id", MemberId(self.member_id))
        object.__setattr__(
            self,
            "responsibility",
            _required_name(self.responsibility, "Responsibility"),
        )
        object.__setattr__(self, "scope_id", _required_name(self.scope_id, "Scope ID"))


@dataclass(frozen=True, slots=True)
class ResponsibilityConflict:
    """Finding that one member holds two incompatible assignments in a scope."""

    member_id: str
    scope_id: str
    responsibilities: tuple[str, str]
    assignment_ids: tuple[str, str]


class ResponsibilityConflictChecker:
    """Report configured same-member, same-scope responsibility conflicts."""

    def __init__(
        self,
        conflicting_pairs: Iterable[tuple[str, str]],
    ) -> None:
        pairs: set[frozenset[str]] = set()
        for first, second in conflicting_pairs:
            first_name = _required_name(first, "Responsibility")
            second_name = _required_name(second, "Responsibility")
            if first_name == second_name:
                raise ValueError(
                    "A conflict pair must contain distinct responsibilities."
                )
            pairs.add(frozenset((first_name, second_name)))
        self._conflicting_pairs = frozenset(pairs)

    def find_conflicts(
        self,
        assignments: Iterable[ResponsibilityAssignment],
    ) -> tuple[ResponsibilityConflict, ...]:
        """Return deterministic findings without rejecting any assignment.

        Raises:
            ValueError: If assignment identifiers are duplicated.
        """
        assignment_list = tuple(assignments)
        assignment_ids = [item.assignment_id for item in assignment_list]
        if len(set(assignment_ids)) != len(assignment_ids):
            raise ValueError("Responsibility assignment identifiers must be unique.")

        grouped: dict[tuple[str, str], list[ResponsibilityAssignment]] = {}
        for assignment in assignment_list:
            grouped.setdefault((assignment.scope_id, assignment.member_id), []).append(
                assignment
            )

        findings: list[ResponsibilityConflict] = []
        for (scope_id, member_id), member_assignments in sorted(grouped.items()):
            ordered = sorted(
                member_assignments,
                key=lambda item: (item.responsibility, item.assignment_id),
            )
            responsibility_names = [item.responsibility for item in ordered]
            if len(set(responsibility_names)) != len(responsibility_names):
                raise ValueError(
                    "A member cannot hold duplicate responsibility assignments "
                    "within the same scope."
                )
            for first, second in combinations(ordered, 2):
                pair = frozenset((first.responsibility, second.responsibility))
                if pair not in self._conflicting_pairs:
                    continue
                responsibilities = (
                    min(first.responsibility, second.responsibility),
                    max(first.responsibility, second.responsibility),
                )
                assignment_by_responsibility = {
                    first.responsibility: first.assignment_id,
                    second.responsibility: second.assignment_id,
                }
                first_name, second_name = responsibilities
                findings.append(
                    ResponsibilityConflict(
                        member_id=member_id,
                        scope_id=scope_id,
                        responsibilities=responsibilities,
                        assignment_ids=(
                            assignment_by_responsibility[first_name],
                            assignment_by_responsibility[second_name],
                        ),
                    )
                )
        return tuple(findings)


__all__ = [
    "ResponsibilityAssignment",
    "ResponsibilityConflict",
    "ResponsibilityConflictChecker",
]
