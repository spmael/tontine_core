"""Public package interface for tontine-core."""

from datetime import date

__version__ = "0.1.0"

from .contributions import ContributionCycle
from .exceptions import TontineError
from .groups import Group


def create_group(
	group_id: str,
	name: str,
	base_currency: str,
	jurisdiction: str | None = None,
) -> Group:
	"""Create a draft group with validated identity and base currency.

	Args:
		group_id: Non-empty group identifier without whitespace.
		name: Human-readable group name.
		base_currency: ISO 4217 alpha-3 base currency code.
		jurisdiction: Optional ISO 3166-1 alpha-2 group jurisdiction.

	Returns:
		A validated draft group.
	"""
	return Group.create_draft(group_id, name, base_currency, jurisdiction)


def create_contribution_cycle(
	cycle_id: str,
	start_date: date,
	due_date: date,
	timezone: str,
) -> ContributionCycle:
	"""Create a contribution cycle through the public package boundary."""
	return ContributionCycle(cycle_id, start_date, due_date, timezone)

__all__ = [
	"ContributionCycle",
	"Group",
	"TontineError",
	"__version__",
	"create_contribution_cycle",
	"create_group",
]
