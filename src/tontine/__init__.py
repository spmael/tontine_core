"""Public package interface for tontine-core."""

from datetime import date
from typing import TYPE_CHECKING

__version__ = "0.2.0"

from .contributions import ContributionCycle
from .exceptions import MissingRecordError, TontineError
from .groups import Group

if TYPE_CHECKING:
	from .contributions import ContributionRule


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
	*,
	rule: "ContributionRule | None" = None,
) -> ContributionCycle:
	"""Create a contribution cycle through the public package boundary.

	Args:
		cycle_id: Unique identifier for the contribution period.
		start_date: First date covered by the cycle.
		due_date: Date on which contributions are due.
		timezone: IANA timezone used for cycle dates.
		rule: Optional rule effective on the cycle start date. When provided,
			its contribution penalty settings are applied to the cycle.

	Raises:
		ValueError: If the rule timezone differs from ``timezone`` or the rule
			is not effective by the cycle start date.
	"""
	if rule is not None:
		if timezone != rule.timezone:
			raise ValueError(
				"Cycle timezone must match the contribution rule timezone."
			)
		return ContributionCycle.from_rule(cycle_id, start_date, due_date, rule)
	return ContributionCycle(cycle_id, start_date, due_date, timezone)

__all__ = [
	"ContributionCycle",
	"Group",
	"MissingRecordError",
	"TontineError",
	"__version__",
	"create_contribution_cycle",
	"create_group",
]
