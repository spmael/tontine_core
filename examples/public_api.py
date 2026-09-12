"""Minimal framework-independent public API example."""

from datetime import date
from decimal import Decimal

import tontine
from tontine.classic import ClassicRotation
from tontine.investments import AllocationRule


group = tontine.create_group("tokyo-cameroon", "Tokyo Cameroon Circle", "JPY")
cycle = tontine.create_contribution_cycle(
    "2027-01", date(2027, 1, 1), date(2027, 1, 31), "Asia/Tokyo"
)
rotation = ClassicRotation.from_active_members(("member-a", "member-b"))
allocation = AllocationRule({"cash_reserve": Decimal("100")})

print(group.name, cycle.cycle_id, rotation.recipient_for_cycle(1), allocation.total_percentage)
