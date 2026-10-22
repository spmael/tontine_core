"""Stable identifiers for member identities."""

from __future__ import annotations


class MemberId(str):
    """Strongly-typed member identifier."""

    def __new__(cls, value: str) -> MemberId:
        if not value or not value.strip():
            raise ValueError("Member identifier is required.")
        if any(char.isspace() for char in value):
            raise ValueError("Member identifier cannot contain whitespace.")
        return str.__new__(cls, value)


__all__ = ["MemberId"]
