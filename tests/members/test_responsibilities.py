"""Tests for configurable responsibility conflicts."""

from __future__ import annotations

import pytest

from tontine.members import (
    ResponsibilityAssignment,
    ResponsibilityConflictChecker,
)


def test_conflict_findings_are_same_member_and_scope_only() -> None:
    checker = ResponsibilityConflictChecker([("treasurer", "reviewer")])
    assignments = (
        ResponsibilityAssignment("a-1", "member-1", "treasurer", "group-1"),
        ResponsibilityAssignment("a-2", "member-1", "reviewer", "group-1"),
        ResponsibilityAssignment("a-3", "member-2", "reviewer", "group-1"),
        ResponsibilityAssignment("a-4", "member-1", "reviewer", "group-2"),
    )

    findings = checker.find_conflicts(assignments)

    assert len(findings) == 1
    assert findings[0].member_id == "member-1"
    assert findings[0].scope_id == "group-1"
    assert findings[0].responsibilities == ("reviewer", "treasurer")
    assert findings[0].assignment_ids == ("a-2", "a-1")
    assert len(assignments) == 4


def test_conflict_pair_order_is_irrelevant_and_findings_are_deterministic() -> None:
    checker = ResponsibilityConflictChecker(
        [("reviewer", "treasurer"), ("treasurer", "reviewer")]
    )
    assignments = [
        ResponsibilityAssignment("review", "member-1", "reviewer", "group-1"),
        ResponsibilityAssignment("treasury", "member-1", "treasurer", "group-1"),
    ]

    finding = checker.find_conflicts(reversed(assignments))[0]

    assert finding.responsibilities == ("reviewer", "treasurer")
    assert finding.assignment_ids == ("review", "treasury")


def test_assignments_without_a_configured_conflict_are_accepted() -> None:
    checker = ResponsibilityConflictChecker([])
    assignments = [
        ResponsibilityAssignment("a-1", "member-1", "chair", "group-1"),
        ResponsibilityAssignment("a-2", "member-1", "treasurer", "group-1"),
    ]

    assert checker.find_conflicts(assignments) == ()


def test_duplicate_and_repeated_member_scope_assignments_fail() -> None:
    checker = ResponsibilityConflictChecker([("reviewer", "treasurer")])
    assignments = [
        ResponsibilityAssignment("same", "member-1", "reviewer", "group-1"),
        ResponsibilityAssignment("same", "member-1", "treasurer", "group-1"),
    ]
    with pytest.raises(ValueError, match="identifiers must be unique"):
        checker.find_conflicts(assignments)

    duplicate_responsibilities = [
        ResponsibilityAssignment("a-1", "member-1", "reviewer", "group-1"),
        ResponsibilityAssignment("a-2", "member-1", "reviewer", "group-1"),
    ]
    with pytest.raises(ValueError, match="duplicate responsibility"):
        checker.find_conflicts(duplicate_responsibilities)


@pytest.mark.parametrize(
    ("assignment_id", "member_id", "responsibility", "scope_id"),
    [
        (" ", "member-1", "reviewer", "group-1"),
        ("a-1", " ", "reviewer", "group-1"),
        ("a-1", "member-1", " ", "group-1"),
        ("a-1", "member-1", "reviewer", " "),
    ],
)
def test_invalid_responsibility_assignment_is_rejected(
    assignment_id: str,
    member_id: str,
    responsibility: str,
    scope_id: str,
) -> None:
    with pytest.raises(ValueError):
        ResponsibilityAssignment(assignment_id, member_id, responsibility, scope_id)


def test_conflict_configuration_rejects_blank_or_same_responsibility_pair() -> None:
    with pytest.raises(ValueError, match="distinct"):
        ResponsibilityConflictChecker([("reviewer", "reviewer")])
    with pytest.raises(ValueError, match="required"):
        ResponsibilityConflictChecker([("", "treasurer")])
