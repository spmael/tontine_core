from datetime import date
from decimal import Decimal

import pytest

from tontine.contributions import ContributionCycle
from tontine.repositories import CycleRepository, InMemoryCycleRepository


def cycle(cycle_id: str) -> ContributionCycle:
    return ContributionCycle(
        cycle_id=cycle_id,
        start_date=date(2027, 1, 1),
        due_date=date(2027, 1, 31),
        timezone="UTC",
    )


def test_cycle_repository_lists_cycles_deterministically() -> None:
    repository: CycleRepository = InMemoryCycleRepository()
    repository.add(cycle("cycle-b"))
    repository.add(cycle("cycle-a"))

    assert [item.cycle_id for item in repository.list()] == ["cycle-a", "cycle-b"]
    assert repository.get("cycle-a").expected_total == Decimal("0")

    with pytest.raises(ValueError, match="already"):
        repository.add(cycle("cycle-a"))

    with pytest.raises(KeyError, match="not found"):
        repository.get("missing")
