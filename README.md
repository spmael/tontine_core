# tontine-core

Build a simple, transparent, auditable, and reusable Python engine for community
tontines.

## Package Identity

- Distribution name: `tontine-core`
- Python import name: `tontine`
- Supported Python: 3.12+

## Development

This repository uses [uv](https://docs.astral.sh/uv/) to create the isolated
environment, resolve dependencies, run tools, and build the package.

```bash
uv sync
uv run pytest
uv run pytest --cov=tontine --cov-report=html --cov-report=term
uv run ruff check src tests
uv run mypy src
uv build
```

Import the package with:

```python
import tontine
```

The core package is framework-independent and has no runtime dependency on a
database, web framework, payment provider, or financial institution.

## Capabilities

The package provides focused, composable domain primitives rather than one
large application object:

- **Groups and members:** validated groups, optional jurisdiction metadata,
  member roles, residence metadata, membership start dates, and lifecycle
  transitions.
- **Contributions:** daily, weekly, and monthly rules; contribution cycles;
  pending, paid, partial, late, and missed statuses; outstanding totals; and
  separate fixed penalty assessments.
- **Classic tontines:** deterministic member rotations, expected payouts,
  duplicate-payout protection, and configurable unpaid-contribution policy.
- **Investment tracking:** allocation schedules, asset definitions, manual
  valuations, purchases, sales, income, fees, and supplied FX-rate records.
- **Ownership and liabilities:** Decimal member-unit issuance and redemption,
  ownership percentages, member values, and manually supplied liability
  records aggregated by currency.
- **Ledger and audit:** balanced double-entry journals, derived balances,
  reversals, adjustments, immutable audit events, and provenance fields.
- **Governance:** versioned rulesets, rotation proposals, one-member-one-vote
  decisions, approval thresholds, and effective rotations.
- **Reporting and repositories:** structured member/group statements and typed
  in-memory repository implementations suitable for application adapters.

## Quick Start

Create a group and a cycle through the top-level API:

```python
from datetime import date

import tontine

group = tontine.create_group(
	"tokyo-cameroon",
	"Tokyo Cameroon Circle",
	"JPY",
	jurisdiction="JP",
)
cycle = tontine.create_contribution_cycle(
	"2027-01",
	date(2027, 1, 1),
	date(2027, 1, 31),
	"Asia/Tokyo",
)
```

### Members and contributions

```python
from datetime import date, datetime, timezone
from decimal import Decimal

from tontine.contributions import ContributionCycle
from tontine.members import Member, MemberRole

member = Member.create(
	"member-001",
	"Amina",
	MemberRole.MEMBER,
	date(2027, 1, 1),
	residence_country="CM",
)

cycle = ContributionCycle(
	"2027-02",
	date(2027, 2, 1),
	date(2027, 2, 15),
	"Africa/Lagos",
	grace_period_days=2,
	late_penalty=Decimal("500"),
)
cycle.add_expected_contribution(member.member_id, Decimal("30000"))
record = cycle.record_contribution(
	member.member_id,
	Decimal("30000"),
	payment_date=datetime(2027, 2, 18, tzinfo=timezone.utc),
)
assert record.penalty == Decimal("500")
assert record.penalty_record.destination.value == "common_reserve"
```

Penalties are group money, separate from contributions, and do not create
investment units. The default destination is `COMMON_RESERVE`.

### Classic rotation

```python
from tontine.classic import ClassicRotation

rotation = ClassicRotation.from_active_members(("member-001", "member-002"))
assert rotation.recipient_for_cycle(1) == "member-001"
expected_pool = rotation.expected_payout(
	{"member-001": Decimal("30000"), "member-002": Decimal("30000")}
)
```

### Investment ownership and liabilities

```python
from tontine.investments import (
	InvestmentValuation,
	Liability,
	LiabilityRegistry,
	MemberUnitLedger,
)

liabilities = LiabilityRegistry()
liabilities.record(
	Liability("fee-001", Decimal("100"), "JPY", date(2027, 2, 1), "invoice")
)
valuation = InvestmentValuation.from_liabilities(
	assets=Decimal("10000"),
	liabilities=liabilities,
	currency="JPY",
	units_outstanding=Decimal("100"),
	asset_currency="JPY",
)

units = MemberUnitLedger()
member_units = units.issue("member-001", Decimal("3000"), valuation.unit_price, "issue-001")
ownership = valuation.member_ownership_percentage(member_units)
value = valuation.member_value(member_units)
```

The valuation derives `NAV = assets - liabilities`, unit price, ownership
percentage, and member value from explicit Decimal inputs. Asset and activity
aggregation remains the responsibility of the consuming application.

### Structured reporting

```python
from tontine.reporting import InvestmentSummary, build_member_statement

investment = InvestmentSummary.from_valuation(valuation, member_units, "JPY")
statement = build_member_statement(
	"member-001",
	"Amina",
	"JPY",
	contributions=(),
	payouts=(),
	investment=investment,
)
assert statement.investment.ownership_percentage == ownership
```

Application layers can turn these structured records into web pages, exports, or
other user interfaces without adding presentation dependencies to the core.

## Structured Reporting

Reporting APIs expose structured member and group statement data, including
contribution history, outstanding amounts, payouts, investment units, ownership,
cash, investments, liabilities, NAV, and proposals. For example, a consumer can
use a `MemberStatement` as the source for a web view or export. PDF, Excel, HTML,
and web rendering remain application-layer responsibilities.

## Financial Account Registry

The account registry records external custody context only. For example, a bank
account may be represented with `****1234`, `NG`, and a logical ledger identifier
such as `ledger-cash-ngn`. The package does not store credentials, connect to
institutions, retrieve live balances, initiate payments, or move real money.
