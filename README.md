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
  member roles, residence metadata, membership start dates, lifecycle
  transitions, stable cycle-effective participation shares, and configurable
  responsibility-conflict findings. Multiple shares do not multiply a person's
  governance vote.
- **Contributions:** daily, weekly, and monthly rules; contribution cycles;
  pending, paid, partial, late, and missed statuses; outstanding totals; and
  separate fixed penalty assessments.
- **Classic tontines:** deterministic member rotations, expected payouts,
  duplicate-payout protection, and configurable unpaid-contribution policy.
- **Investment tracking:** allocation schedules, asset definitions, manual
  valuations, purchases, sales, income, fees, and supplied FX-rate records.
- **Hybrid rules:** immutable effective-cycle policies for pot/fund shares,
  partial-payment order, catch-up, exit fees, and payout deferral, plus pure
  received-contribution splitting, recorded allocations, pending valuations,
  once-only unit issuance, linked allocation reversals, arrears and catch-up,
  approved member exits, and pure combined settlement positions.
- **Ownership and liabilities:** Decimal member-unit issuance and redemption,
  ownership percentages, member values, and manually supplied liability
  records aggregated by currency.
- **Ledger and audit:** balanced double-entry journals, derived balances,
  reversals, adjustments, immutable audit events, and provenance fields.
- **Governance:** versioned rulesets, rotation proposals, one-member-one-vote
  decisions, approval thresholds, and effective rotations.
- **Reporting and repositories:** structured member/group statements and typed
  in-memory repository implementations suitable for application adapters.

### Participation shares

`ParticipationShare` gives each per-share position a stable ID, an owning member,
and an inclusive effective cycle. `ParticipationShareRegistry` returns active
shares by cycle and resolves a share back to its member. Retiring a share takes
effect at the supplied cycle; it does not rewrite an existing rotation version.
Governance continues to use member IDs, so multiple shares do not create
additional votes.

Use `ContributionCycle.add_expected_share_contribution` and
`record_share_contribution` to track each active share separately. Returned
`ShareContribution` records retain both the share ID and owner member ID.
`ClassicRotation.from_active_shares` creates share-keyed rotations, and
`ClassicRotationSchedule.resolve_member_for_cycle` resolves the selected share
to its owner. For exact same-currency reporting, pass share-keyed `Decimal`
amounts to `ParticipationShareRegistry.roll_up_amounts` with the effective
cycle and ISO 4217 currency code.

Responsibilities are separate from `MemberRole`. Configure
`ResponsibilityConflictChecker` with incompatible pairs and call
`find_conflicts` to receive deterministic same-member, same-scope findings;
findings do not reject assignments or enforce application permissions.

```python
from datetime import UTC, date, datetime
from decimal import Decimal

from tontine.classic import ClassicRotation, ClassicRotationSchedule, ClassicRotationVersion
from tontine.contributions import ContributionCycle
from tontine.members import ParticipationShare, ParticipationShareRegistry

shares = ParticipationShareRegistry()
first = ParticipationShare("share-001", "member-001", effective_cycle=1)
second = ParticipationShare("share-002", "member-001", effective_cycle=1)
shares.register(first)
shares.register(second)

cycle = ContributionCycle(
    "2027-01",
    date(2027, 1, 1),
    date(2027, 1, 31),
    "UTC",
)
records = []
for share, amount in ((first, Decimal("100")), (second, Decimal("150"))):
    cycle.add_expected_share_contribution(share, 1, amount)
    records.append(
        cycle.record_share_contribution(
            share,
            1,
            amount,
            as_of=datetime(2027, 1, 15, tzinfo=UTC),
        )
    )

member_totals = shares.roll_up_amounts(
    {
        record.share_id: record.contribution.actual_amount
        for record in records
        if record.contribution.actual_amount is not None
    },
    cycle_number=1,
    currency="XAF",
)
assert next(iter(member_totals.values())) == Decimal("250")

rotation = ClassicRotation.from_active_shares(shares.shares_for_cycle(1), 1)
schedule = ClassicRotationSchedule(
    (
        ClassicRotationVersion(
            1, 1, rotation, source_event="rotation-approved-1"
        ),
    )
)
assert schedule.resolve_member_for_cycle(1, shares) == "member-001"
```

Retiring a share with `shares.retire("share-002", effective_cycle=3)` makes it
inactive from cycle 3 onward; it does not mutate earlier rotation versions.
The rotation still records share IDs, while `resolve_member_for_cycle` resolves
the selected share to its owner. Governance continues to accept member IDs, not
share IDs.

```python
from tontine.members import (
    ResponsibilityAssignment,
    ResponsibilityConflictChecker,
)

checker = ResponsibilityConflictChecker([("treasurer", "reviewer")])
findings = checker.find_conflicts(
    (
        ResponsibilityAssignment(
            "assignment-1", "member-001", "treasurer", "group-1"
        ),
        ResponsibilityAssignment(
            "assignment-2", "member-001", "reviewer", "group-1"
        ),
    )
)
assert len(findings) == 1
assert findings[0].responsibilities == ("reviewer", "treasurer")
```

### Hybrid policy schedules

```python
from decimal import Decimal

from tontine.hybrid import (
    HybridRule,
    HybridRuleSchedule,
    HybridRuleVersion,
    split_contribution,
)

rule = HybridRule(
    currency="XAF",
    fund_share_bps=3000,
    launch_unit_price=Decimal("1000"),
    max_valuation_age_days=30,
)
schedule = HybridRuleSchedule(
    group_id="community-1",
    versions=(HybridRuleVersion(1, effective_cycle=1, adopted_cycle=0, rule=rule),),
)
assert schedule.version_for_cycle(1).rule.fund_share_bps == 3000
pot, fund = split_contribution(Decimal("12345"), "XAF", 3000)
assert (pot, fund) == (Decimal("8642"), Decimal("3703"))
```

Use `schedule.with_version(version, current_cycle=...)` to add a future version
without mutating history. Cycle zero means setup. Fee changes require a complete
intervening cycle of notice: a fee adopted in cycle 2 can first apply in cycle 4.
Constructing a schedule restores recorded versions; it does not establish the
current cycle or validate governance approval. Prices are exact `Decimal` values
in currency units per investment unit, and fees are percentages of gross unit
value. Rule policies do not move funds. `split_contribution`
splits the amount actually received into `(pot, fund)`; the fund share rounds
down to the currency's smallest unit and the pot receives the exact remainder.
`HybridAllocationRegistry` records allocation inputs and outcomes, retains
fund shares pending a usable valuation when units are already outstanding, and
issues rounded units through `MemberUnitLedger` using the allocation identifier
as the unit event reference.

`HybridAllocationRegistry.snapshot()` captures resolved and pending records,
rule provenance, reversals, exit freezes, and its audit events. Restore it with
`HybridAllocationRegistry.from_snapshot(snapshot, unit_ledger=...)` after
restoring the matching unit-ledger snapshot.
`HybridArrearsRegistry.snapshot()` preserves closed-cycle identities, arrears
events, and audit provenance; restore it with the matching allocation registry
and unit ledger.
`HybridExitRegistry.snapshot()` preserves exit settlements, payout queue reports,
and audit provenance. Restore it with the matching allocation, arrears, and
unit-ledger state; restoration validates recorded references without rerunning
governance approval, valuation, settlement, or payment workflows.

The ledger keeps immutable posted journals as its source of truth and maintains
current account/currency balances as a derived projection. `balance_for` accepts
an optional timezone-aware `as_of` instant; reversals and adjustments affect
historical balances from their own `recorded_at` timestamps. Use
`InMemoryLedgerRepository.rebuild_balance_projection()` to validate and rebuild
the current and historical projections from `journals()`.

`HybridSettlementHistory.from_registries` snapshots allocation, arrears, and
exit records alongside contribution cycles, payouts, and the rule schedule.
`settlement_position(history, member, valuation)` derives current dues, the
rotation-pot amount paid in versus payouts received, member units and their
value, and explicit pending allocations, pending exits, elections, and offsets.
The member-statement presentation orders the rotation pot ahead of "member
funds: redeemable" and derives the unit liability flag from statute facts. The
domain position keeps the facts and calculated amounts, not the classification.
Pass the resulting position to
`build_member_statement(..., hybrid_position=position)` to include it in a
structured member report. The calculation stores no balances and initiates no
payments.

### Hybrid allocation persistence and audit

Persistence adapters can implement `tontine.repositories.AllocationRepository`.
The contract stores one immutable pending or resolved allocation per
`contribution_id`; a pending record may transition once to a resolved record
only when allocation and contribution identifiers and all receipt, rule, and
split provenance remain unchanged. Missing keys raise `MissingRecordError`,
duplicate contribution keys raise `ValueError`, and listings are sorted by
contribution identifier. The in-memory implementation is
`InMemoryAllocationRepository`.

Adapters must enforce a unique constraint on `contribution_id` in persistent
storage, including transactions racing to record the same receipt. The shared
contract checks are in
[`tests/repositories/allocation_repository_contract.py`](./tests/repositories/allocation_repository_contract.py);
adapter tests can call `assert_allocation_repository_contract` with a factory
for their repository implementation. For example, import the helper from the
core checkout's `tests/repositories` directory in an adapter test and call
`assert_allocation_repository_contract(KoloAllocationRepository)`. Run that
adapter test with `uv run pytest tests/repositories/test_kolo_allocation_repository.py`;
run the core implementation's contract test with
`uv run pytest tests/repositories/test_allocation_repository_contract.py`.
The Kolo adapter migration and database-specific uniqueness constraint remain
in that adapter project; no database or Kolo code belongs in this package.

Pass the same `AuditEventRegistry` to the allocation, arrears, and exit
registries when a consumer needs one combined in-memory audit stream. Allocation,
pending-resolution, reversal, arrears, election/forfeiture, and exit records
emit stable, append-only audit event identifiers. Since allocation records keep
calendar dates rather than timestamps, their audit timestamps are normalized
to midnight UTC on the relevant effective date; reversals and other timestamped
events retain their recorded timestamps.

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

# Persist snapshots at the adapter boundary; they contain events, not balances.
unit_snapshot = units.snapshot()
restored_units = MemberUnitLedger.from_snapshot(unit_snapshot)
```

The schema-v1 unit snapshot preserves ordered issue and redemption events rather
than cached balances. ADR-007 defines this event history as the unit state used
when restoring hybrid registries.

The valuation derives `NAV = assets - liabilities`, unit price, ownership
percentage, and member value from explicit Decimal inputs. Before the first
unit issue, `units_outstanding` may be zero: NAV is still derived and
`has_units_outstanding` is false, while unit price, ownership percentage, and
member value are `None`. Asset and activity aggregation remains the
responsibility of the consuming application.

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
