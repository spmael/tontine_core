# Tontine-Core Gaps — Patch Wishlist For Next Version

## 1. Purpose

This is a working list of real friction points found in `tontine-core` 0.1.0 while building Kolo against it — places where the integrating Django app had to add its own workaround, duplicate logic the engine could reasonably own, or hand-roll a capability the BRD assumed the engine would eventually support. It is written for the library's own next-version patch work, not for Kolo's backlog — every item here is scoped to `tontine-core` itself, not to Kolo's Django code.

Each item states what the library does today (with the exact method/behavior, verified against the installed `0.1.0` package), why it created friction for an integrating application, and a suggested patch direction. None of these are blocking Kolo's V1 — each has a working Kolo-side workaround already in place — but every one is real, hit-in-practice friction, not speculation.

## 2. How This List Was Produced

Found by actually building Kolo's Contributions, Rotation, Governance, Investments, Ledger, and Statements capabilities against the installed package, then tracing every workaround, every generic/unhelpful error message, and every piece of logic Kolo had to invent that arguably belongs closer to the domain engine. Cross-referenced against `docs/TONTINE_CORE_PRIMITIVES_v1.md` (the verified inventory of what the package actually exposes) and the BRD's own assumptions about what the engine would provide.

Items marked **(design-time)** came from designing post-V1 stories (membership duties, investment-decision votes, investment activity, reconciliation; KOLO-054 to KOLO-057), not from built code. The engine behaviour each one describes was still verified against the installed package. The "workaround" for these is the planned Kolo-side approach in that story, not shipped code.

## 3. Cross-Cutting: No Persistence Or Incremental-State Story

This is the single biggest theme across three separate modules (`tontine.governance`, `tontine.ledger`, and implicitly `tontine.classic`'s rotation-versioning gap in Section 5): every stateful engine object (`GovernanceRegistry`, `InMemoryLedgerRepository`) is designed to live and die within one Python call. Nothing in the library serializes, snapshots, or incrementally updates that state. An integrating application that persists its own domain rows (as any real app must) is left to **fully replay history through a fresh in-memory object on every single read or write**, with no cheaper path offered.

Concretely, in Kolo:

- `ledger/services.py::balance_for()` replays **every posted journal for the group** through a fresh `InMemoryLedgerRepository` to answer one balance query — there is no incremental running balance anywhere in the library. This is `O(n)` in a group's total journal history for every single balance check, on every page load that shows a balance (Overview, Rotation, Statements, Ledger itself).
- `governance/services.py::_rehydrate_registry_for()` rebuilds a fresh `GovernanceRegistry`, then replays `create_rotation_proposal` → `open_proposal` (if opened) → every `vote()` in vote order, just to get back to a valid state before calling `evaluate()` or accepting one more vote. This happens on **every** governance action against an existing proposal.
- The rehydration replay is also fragile: `create_rotation_proposal` re-validates the candidate order against the group's *current* Active membership roster (see Section 4.1's `set(rotation.member_ids) != self._active_members` check). If a member's status changed since the proposal was first created — including a Suspend/Activate that has nothing to do with the proposal itself — replaying it now raises, and Kolo has to catch this as "this group's active membership has changed since this proposal was created, so it can no longer be acted on," discarding an otherwise-valid in-flight proposal.

**Suggested patch direction:** give `GovernanceRegistry` and `InMemoryLedgerRepository` (and any future stateful registry) an explicit snapshot/restore pair — e.g. `to_state()` / `from_state(state)` — so an integrating app can persist and rehydrate the engine's own state directly instead of replaying every domain event through the constructor and every mutating method on every call. Even a documented event-sourcing contract (a defined minimal event shape the app must store, with a single `replay(events)` classmethod) would remove the need for each integrator to reinvent this, and would make the "roster changed since proposal was created" failure mode a deliberate, documented one rather than a surprise.

## 4. Governance (`tontine.governance`)

### 4.1 No single-cycle "exception" proposal — every change requires a full future order

`GovernanceRegistry.create_rotation_proposal(...)` is the *only* proposal-creation primitive the module exposes (confirmed via `inspect` — the full public method list is `create_rotation_proposal`, `open_proposal`, `vote`, `evaluate`, `rotation_for_cycle`, `audit_events`, `add_ruleset`, `ruleset_for_cycle`). It requires:

```python
if set(rotation.member_ids) != self._active_members:
    raise ValueError("Proposed rotation must contain all active members.")
```

— meaning **every** proposal must supply a complete candidate order listing every single Active member, even when the actual intent is a one-line change: inserting a newly activated member into the current round, or swapping two people for a single upcoming cycle.

Kolo's own BRD (§13.9) anticipated a second, lighter-weight proposal type for exactly this — "Rotation Exception Proposal: adding a newly activated member to the current rotation round" — but there is no engine-level primitive to build it against. Kolo's `ProposalType.ROTATION_EXCEPTION` exists only as a schema value today with "its own behavior deferred to a later story," precisely because the engine has nothing to call.

**Suggested patch direction:** add a second, narrower proposal primitive — e.g. `create_rotation_exception_proposal(proposal_id, ..., target_cycle: int, insert_member_id: str, position: int)` — that only needs the one member/position being changed, validates it against the *existing* rotation for that cycle rather than requiring a brand-new full order, and applies (on approval) as a one-cycle override that the base order resumes after. This is the exact capability referenced by name in this list's title.

### 4.2 One combined, non-specific validation error

```python
if effective_cycle < 1 or voting_deadline < created_at:
    raise ValueError("Proposal cycle and dates are invalid.")
```

Two unrelated conditions — an out-of-range cycle number, and a deadline that's already passed — share one generic message. An integrating app cannot show the user *which* field was wrong without independently re-deriving both checks itself before ever calling the engine (which is exactly what Kolo had to do — see `CreateProposalForm.clean_effective_period`/`clean_voting_deadline` in the Kolo codebase, added specifically to give users a real error instead of this one).

**Suggested patch direction:** raise a distinct exception (or distinct message) per condition — e.g. `InvalidEffectiveCycleError` vs. `InvalidVotingDeadlineError` — or attach a machine-readable `reason` to a single exception type so callers can branch on it without re-implementing the check.

### 4.3 No awareness of "cycles already reached"

`effective_cycle` is validated only as `>= 1`. The engine has no concept of which cycle a group has actually reached in real time (it is stateless per Section 3), so it happily accepts an `effective_cycle` that refers to a period that has already closed or is already in progress — even though the BRD's own intent (and Kolo's own UX, after a user-reported bug) is that an approved change only ever applies to a **future** period.

Today, Kolo computes and enforces "must be later than the group's current period" entirely on its own side (`CreateProposalForm.__init__`/`clean_effective_period`), with no help from the engine.

**Suggested patch direction:** either accept an explicit `current_cycle: int` parameter in `create_rotation_proposal` so the engine can enforce `effective_cycle > current_cycle` itself, or explicitly document in the method's docstring that this validation is the integrating application's responsibility (right now the docstring only says "Raises: ValueError: If identity, threshold, dates, or rotation order is invalid," which reads as if cycle-ordering *is* covered).

### 4.4 Membership-roster drift breaks in-flight proposals (see Section 3)

Covered under the cross-cutting persistence gap above — restated here because it's specifically a governance-module symptom: replaying a proposal's history against the group's *current* Active roster (rather than the roster at proposal-creation time) means an unrelated Suspend/Activate elsewhere in the group can silently invalidate an open proposal the next time anyone tries to vote on or evaluate it.

### 4.5 Proposals are rotation-only: no generic decision proposal (design-time)

`RotationProposal` is the only proposal type, and `create_rotation_proposal` is the only way to create one. Every proposal must carry a full `rotation_order`, and approval always writes that order into `_rotations`. A group that wants to vote on anything else, such as an investment decision ("buy up to ¥200,000 of X"), a rule change, or accepting a new agreement version, cannot use the registry at all.

Kolo's planned investment-decision proposals will therefore be counted entirely in Django, duplicating the engine's one-vote-per-eligible-member logic. That gives two vote implementations whose behaviour can drift apart.

**Suggested patch direction:** separate the voting core from what happens on approval. For example, a generic `Proposal` (id, title, description, proposer, approval rule, deadline, votes, status, and an opaque `subject: Mapping[str, str]`), with `create_decision_proposal(...)` that does nothing on approval beyond becoming `APPROVED`. `RotationProposal` then becomes one subject type whose approval also registers a rotation. `vote`/`evaluate` stay shared.

### 4.6 Approval is only "yes votes ÷ eligible members ≥ threshold": no quorum, no participation rule, no tally (design-time)

`evaluate()` computes `yes / len(active_members) * 100` and compares it to `approval_threshold`. That is the whole rule:

- There is no quorum and no "every member must have voted" option. An investment club relying on all members taking part in decisions needs "rejected until everyone has recorded yes/no/abstain", which cannot be expressed here.
- Abstain and not voting are treated the same. Neither counts toward the yes percentage, and the engine never distinguishes them.
- `evaluate()` returns only a `ProposalStatus`, not the tally behind it. Kolo already recounts yes votes and eligible members in Django to build its result summary (`governance/services.py::evaluate_proposal`).

**Suggested patch direction:** an `ApprovalRule` value object (`threshold`, optional `quorum_percentage`, `require_full_participation`, whether abstain counts toward quorum), plus `evaluate()` returning an `EvaluationResult` with `status` and a tally (`yes`, `no`, `abstain`, `not_voted`, `eligible`) and a reason when rejected for quorum or participation. The current behaviour stays the default rule.

### 4.7 `vote()` and `evaluate()` ignore `voting_deadline`

`create_rotation_proposal` validates `voting_deadline`, but nothing afterwards reads it. `vote()` accepts a vote after the deadline, and `evaluate()` will close a proposal before the deadline even when members have not voted yet. Neither method takes a "now" to compare against.

Kolo enforces the deadline itself (`governance/services.py::cast_vote` rejects a vote once `timezone.now() > proposal.voting_deadline`).

**Suggested patch direction:** take an explicit `at: datetime` on `vote()` and `evaluate()`. Reject a vote after the deadline, and refuse early evaluation unless every eligible member has voted, or make early evaluation an explicit flag.

### 4.8 Audit timestamps come from `datetime.now()`, so replayed history gets new timestamps

`vote()`, `evaluate()`, and `add_ruleset()` stamp their audit events with `datetime.now().astimezone()`, and there is no parameter to supply the real time. Combined with Section 3, every rehydration replay re-creates the proposal's audit events stamped with the time of the replay. The engine's own `audit_events()` for a persisted proposal therefore never reflects when anything actually happened. Kolo records its own audit trail instead (`audit.services.record_event`).

**Suggested patch direction:** accept `occurred_at` (or an injectable clock) on every mutating method, matching how `create_rotation_proposal` already takes `created_at`.

## 5. Rotation (`tontine.classic`)

### 5.1 Multi-version rotation resolution exists, but only trapped inside Governance's full replay cost

`ClassicRotation` itself represents exactly **one** static order — no version history, no "which order applies to cycle N when several have existed over time" concept. That resolution logic *does* exist in the library, but in a different module entirely: `GovernanceRegistry.rotation_for_cycle(cycle_number)`, confirmed by reading the source:

```python
def rotation_for_cycle(self, cycle_number: int) -> ClassicRotation:
    """Return the latest approved rotation effective for a cycle."""
    applicable = [cycle for cycle in self._rotations if cycle <= cycle_number]
    ...
```

This is exactly "largest effective-from-cycle at or before the requested cycle" — the same resolution Kolo needs for routine, high-traffic reads (who receives this period's payout, what does the Rotation page show, what does the dashboard's "current recipient" card say). But reaching it requires a live `GovernanceRegistry`, which (per Section 3) is stateless and only knows what's been replayed into it — every proposal ever created, opened, voted on, and evaluated for the group. Rehydrating a group's *entire governance history* just to answer "who's up next this cycle" is wildly disproportionate for a read with nothing to do with governance UI, so Kolo doesn't use it at all — it rebuilt the same resolution from scratch, cheaply, directly against its own persisted rotation-round rows:

```python
rotation_round = (
    group.rotation_rounds.filter(effective_from_period__lte=period_number)
    .order_by("-effective_from_period")
    .first()
)
```

**Suggested patch direction:** extract this resolution out of `GovernanceRegistry` into a standalone, lightweight type — e.g. a `RotationTimeline`/`VersionedRotation` built directly from a list of `(effective_from_cycle, ClassicRotation)` pairs, with no governance/proposal/vote history required to construct it — living in `tontine.classic` alongside `ClassicRotation` itself. `GovernanceRegistry.rotation_for_cycle` could then delegate to it internally. That would let an integrator answer "who receives cycle N" cheaply, without paying Section 3's full-replay cost just to read a rotation order.

## 6. Contributions (`tontine.contributions`)

### 6.1 Penalty destination is not configurable

Every engine-derived `Penalty` from a late/missed contribution always carries the dataclass default `common_reserve` as its destination, regardless of what a group's own contribution rule configures (Kolo's BRD supports `common_reserve`, `social_fund`, `administration_fund`, `distribute_at_cycle_end`, `compensate_affected_member` as configurable destinations). There is no constructor or method parameter on the contribution-recording path to pass a different destination through.

Kolo works around this by discarding the engine's own `Penalty.destination` and overwriting `PenaltyRecord.destination` from the group's `rule_version.penalty_destination` immediately after — confirmed live during KOLO-023: a rule configured for `social_fund` still produced an engine-derived `Penalty` reporting `common_reserve`, silently wrong unless the caller knows to override it.

**Suggested patch direction:** accept a `penalty_destination` parameter wherever a `Penalty` is derived (e.g. on `record_contribution` or the cycle's penalty-derivation path) so the returned `Penalty.destination` is authoritative and callers don't need a documented "always override this" workaround.

### 6.2 Strict timezone-aware datetime requirement is an easy, silent trap

Any naive `datetime` passed where the engine expects a timestamp (contribution `payment_date`, proposal `created_at`/`voting_deadline`, etc.) is rejected with `ValueError: Contribution timestamps must be timezone-aware.` The strictness itself is reasonable, but it's an easy integration trap: Django's plain `forms.DateTimeField` (as opposed to a `ModelForm` field bound to a `DateTimeField` model field) produces a **naive** datetime by default, so this fails the first time a plain form is used, with no hint in the error about where the timezone should come from or what format is expected.

**Suggested patch direction:** either accept a naive datetime and interpret it as UTC (with a clear warning, not a raise), or make the message name the exact parameter and a concrete fix ("`payment_date` must be timezone-aware — see `datetime.timezone.utc` or `zoneinfo`"), or ship a small `ensure_aware(dt, tz=UTC)` helper alongside the public API so integrators aren't left to build their own (Kolo did: a shared `_as_aware_datetime()` helper used by three separate forms).

## 7. Investments (`tontine.investments`)

### 7.1 `InvestmentValuation` raises on the normal "zero units outstanding" state

```python
if self.units_outstanding == 0:
    raise ValueError("Units outstanding must be greater than zero.")
```

This guards a real division-by-zero (unit price = NAV / units outstanding), but zero units outstanding is not an edge case — it's the **default starting state** of every group until its first unit issuance, and the state of any group that has investment tracking enabled but hasn't issued anything yet. Every caller that wants to gracefully show "no investment activity yet" (as opposed to crashing) has to wrap every valuation call in `try/except ValueError`, which Kolo does throughout `investments/services.py` and `statements/services.py`.

**Suggested patch direction:** offer an explicit empty/zero representation for this state — either a `ValuationResult` that's a tagged union (`Empty` vs. `Valued`), or a documented, dedicated `InvestmentValuation.empty(currency)` constructor with `nav == 0`, `unit_price == 0`, `member_value(...) == 0` — instead of requiring every integrator to catch an exception for what is, in practice, the common case for a new or lightly-used group.

### 7.2 `InvestmentActivityRegistry` can store activity but not read it back (design-time)

The registry's only public method is `record_activity`. There is no `activities_for(asset_id)`, no date-range query, and no total per type. An integrator that records activity must keep and query its own copy for every read, such as "all purchases of X this quarter" or "income received this year", which leaves the registry useful only as a validator.

**Suggested patch direction:** add read methods (`activities(asset_id=None, event_type=None, start=None, end=None)` and `total(event_type, currency, ...)`), or document that the registry is validation-only.

### 7.3 Activity is not checked against its asset (design-time)

Verified live: `record_activity('e1', 'purchase', <JPY asset>, 0, 'USD', ...)` succeeds. A USD purchase is recorded against a JPY asset, and a zero-amount purchase is accepted, because `record_activity` copies `asset.asset_id` but never compares `currency` with `asset.currency`, and `_non_negative` allows `0`.

**Suggested patch direction:** reject a currency that differs from the asset's, or require an explicit FX rate when they differ. Require `amount > 0` for `purchase`/`sale`/`income`. Allow `0` only where it has a meaning, if anywhere.

### 7.4 Activity has no reference to the decision that approved it (design-time)

`InvestmentActivity` carries only `source` (free text). There is no structured field linking a purchase or sale to the approval behind it, so an engine-level check like "every purchase or sale traces to an approved decision" cannot be written. Kolo plans to hold this link in its own `InvestmentActivityRecord.decision` field.

**Suggested patch direction:** an optional `authorization_ref: str | None` on `InvestmentActivity`. Once Section 4.5 exists, it could be validated against an approved decision proposal in the same group.

## 8. Ledger (`tontine.ledger`)

### 8.1 Every balance query replays the group's entire journal history

Covered in Section 3 as the clearest single example of the cross-cutting persistence gap: `InMemoryLedgerRepository` has no incremental running-balance concept, so `balance_for()` is `O(total journals ever posted)` on every call, with no cheaper path. This is the same architectural gap as Section 4.4/Section 3's governance replay, restated here because it's the module where the performance cost is most visible in practice (every page in Kolo that shows a cash balance, NAV, or ledger figure pays this cost on every load).

### 8.2 `adjust()`/`reverse()` raise a bare `KeyError`, breaking the library's own error-translation contract

`InMemoryLedgerRepository.adjust()` and `.reverse()` both resolve their `original_journal_id` argument through a private `_journal_for()` helper — verified live via `inspect.getsource` — that raises a bare Python `KeyError` when the referenced journal isn't found in the repository, not a `tontine.errors.TontineError` (or any subclass of it) the way essentially every other validation failure in the library does. This matters because Kolo's own adapter layer, `core_adapter.services.accounts.adjust_journal`, relies on a single `translate_core_errors()` wrapper to catch every engine exception and turn it into a readable `ValidationError` for Django — and that wrapper only catches `TontineError`. A bare `KeyError` sails straight through it uncaught, which would surface to a caller as an unhandled 500 rather than the same graceful "the engine rejected this" path every other validation failure gets.

Kolo's workaround, in `ledger/services.py`'s `propose_journal_correction()` and `approve_journal_correction()`: replay the group's full posted history first so the referenced journal is essentially always found by the time `adjust_journal` is called, *and* defensively catch `KeyError` alongside `CoreAdapterError` at every call site anyway, since the replay-first approach only reduces the odds of hitting this, it doesn't eliminate the underlying inconsistency in the library itself.

**Suggested patch direction:** have `_journal_for()` (and any other private lookup with the same shape elsewhere in the module) raise a proper `TontineError` subclass — e.g. `JournalNotFoundError` — instead of a bare `KeyError`, so every caller relying on the library's own documented error-translation contract can trust it uniformly, without needing to know which specific internal lookups happen to be exceptions to it.

### 8.3 No point-in-time balance (design-time)

`InMemoryLedgerRepository.balance_for(account_id, currency)` sums every journal in the repository. `JournalEntry` carries no date filter, and there is no `as_of` parameter. Comparing an outside statement dated the 31st with Kolo's balance on the 31st, which is what monthly reconciliation needs, means building a separate replay of only the journals recorded on or before that date.

**Suggested patch direction:** `balance_for(account_id, currency, as_of: datetime | None = None)`, filtering on the journal's own timestamp.

## 9. Members (`tontine.members`)

### 9.1 No concept of a "share": one member id means exactly one slot

Every `member_id` gets exactly one contribution obligation and one rotation entitlement. A person holding two or more shares in a group (BRD-supported, and common in real tontines) has no representation. Kolo derives a separate synthetic engine member id per active share (`core_adapter/mapping/shares.py`, `<member>::share-<n>`) and adds results back together for reporting. Every engine call that is really about a person, not a slot, then needs translating.

**Suggested patch direction:** a `Share`/`Participation` concept under `Member` (member id plus share number) that contributions and rotation operate on, with reporting able to roll up per member. Governance stays per member (Kolo already treats voting as one vote per person, not per share).

### 9.2 Roles are a closed three-value enum with no separate responsibilities (design-time)

`MemberRole` is exactly `member`/`treasurer`/`administrator`, and `Member` has one `role`. A group that assigns working responsibilities, such as an independent reviewer of the Treasurer's records, a secretary, or a research coordinator, has nowhere to put them. Adding a fourth value is not an option for the integrator: Kolo passes its stored role straight into `MemberRole(role)` (`core_adapter/services/groups.py`), so an unknown value would fail to rehydrate. Kolo plans to keep duties in a separate table beside the role.

The engine also has no separation-of-duties rule (for example, the Treasurer must not also be the reviewer who checks the Treasurer). That rule is domain logic, not app authentication, so it fits the engine; `MemberRole`'s own docstring says roles "do not imply application authentication".

**Suggested patch direction:** `Member.responsibilities: frozenset[MemberResponsibility]` (at least `reviewer`, `secretary`), separate from `role`, plus a small `conflicting_assignments(members) -> list[...]` check the integrator can call before saving. Enforcing permissions stays in the app.

## 10. Cross-Cutting: No Bridge Between The Classic Rotation And Investments

`tontine.classic`/`tontine.contributions` and `tontine.investments` are fully independent. Neither imports the other. The only module that touches both is `tontine.reporting`, and it places a member's contributions, payouts, and `InvestmentSummary` side by side without deriving any one from another. Verified in the installed package:

- `MemberUnitLedger.issue(member_id, contribution, unit_price, event_id)` takes `contribution` as a plain number. It has no reference to a recorded contribution, its cycle, or its status.
- `AllocationRule`/`AllocationRuleSchedule` split the *investment pool* across asset categories (cash, bond, equity, …). They do not say what share of a member's *contribution* goes to the rotation pot versus the investment pool.
- Nothing connects a missed or late contribution, or its `Penalty`, to unit issuance. Nothing connects a member's exit from the rotation to their unit balance.

A hybrid group, where each contribution is partly paid out in rotation and partly invested as units, is a common real-world tontine shape. In Kolo today the two sides are joined by hand. The Treasurer retypes the contribution amount and unit price into the "issue units" form, and links the confirmed contribution only through a free-text `source_event` (`investments/services.py::issue_units`). Nothing stops the amount from differing from the confirmed contribution, issuing twice for one contribution, or issuing units for a missed one. Settlement checks before a member leaves (dues, unpaid payout, unit balance) also have to query each side separately in Kolo.

**Suggested patch direction:** a small bridging module (e.g. `tontine.hybrid`) that owns the rules connecting the two:

1. **Contribution split rule:** the percentage of each contribution that goes to the rotation pot versus the investment pool, versioned by effective cycle like `Ruleset`/`AllocationRuleSchedule`.
2. **Issuance derived from a recorded contribution:** `issue_from_contribution(contribution, split_rule, valuation)` computes the invested part and issues units at the valuation's unit price, using the contribution's own event id as the unit event id. That gives one source of truth and makes a duplicate issuance impossible through the existing duplicate-event check.
3. **Missed or late contributions:** a documented rule for what a missed or late contribution does to the investment side (no units, fewer units, or penalty routed to the pool), instead of leaving it undefined.
4. **Exit and settlement:** one `settlement_position(member_id, cycle)` that reports outstanding dues, unpaid rotation entitlement, and unit balance together, plus the rule for what happens to units when a member leaves (forced redemption at the current price, or held until cycle end).
5. **Combined statement inputs:** `tontine.reporting` builds a member's rotation cash position and unit value from the same contribution events, not from figures the integrator passes in separately.

## 11. Summary Table

| # | Module | Gap | Kolo's current workaround |
| --- | --- | --- | --- |
| 3 | Cross-cutting | No persistence/snapshot story for stateful registries | Full event replay on every call (`_rehydrate_registry_for`, `_replay_posted_journals`) |
| 4.1 | Governance | No single-cycle "exception" proposal primitive | `ProposalType.ROTATION_EXCEPTION` exists in schema, unimplemented — deferred |
| 4.2 | Governance | Combined, non-specific date/cycle validation error | Kolo pre-validates both conditions itself before calling the engine |
| 4.3 | Governance | No "current cycle" awareness in `effective_cycle` | Kolo computes and enforces the minimum valid period itself |
| 4.4 | Governance | Roster drift can invalidate an in-flight proposal | Caught and surfaced as a specific error message |
| 4.5 | Governance | Proposals are rotation-only; no generic decision proposal (design-time) | Planned: investment-decision votes counted entirely in Django |
| 4.6 | Governance | Threshold-only approval; no quorum, no participation rule, no tally (design-time) | Kolo recounts the tally itself; planned full-participation check in Django |
| 4.7 | Governance | `vote()`/`evaluate()` ignore `voting_deadline` | Kolo rejects late votes in `cast_vote` |
| 4.8 | Governance | Audit timestamps are `datetime.now()`, so replays get new timestamps | Kolo keeps its own audit trail |
| 5.1 | Rotation | Multi-version resolution exists, but only inside Governance's costly full replay | Kolo's own `round_for_period()`, built from scratch to avoid that cost |
| 6.1 | Contributions | Penalty destination always `common_reserve` | Kolo overwrites `Penalty.destination` after the fact |
| 6.2 | Contributions | Strict tz-aware datetime, easy silent trap | Kolo's shared `_as_aware_datetime()` helper |
| 7.1 | Investments | `InvestmentValuation` raises on zero units outstanding | Kolo wraps every valuation call in `try/except ValueError` |
| 7.2 | Investments | Activity registry cannot read records back (design-time) | Planned: Kolo queries its own `InvestmentActivityRecord` rows |
| 7.3 | Investments | Activity currency not checked against asset; zero amount accepted (design-time) | Planned: Kolo-side validation |
| 7.4 | Investments | Activity has no link to its approving decision (design-time) | Planned: Kolo-side `decision` foreign key |
| 8.1 | Ledger | No incremental balance; full replay every query | Accepted as-is; a real cost at scale, not yet urgent for V1 |
| 8.2 | Ledger | `adjust()`/`reverse()` raise a bare `KeyError`, not a `TontineError`, bypassing the library's own error-translation contract | Replay-first to avoid triggering it, plus a defensive `except (CoreAdapterError, KeyError)` at every call site |
| 8.3 | Ledger | No point-in-time (`as_of`) balance (design-time) | Planned: replay only journals recorded on or before the date |
| 9.1 | Members | No "share" concept; one member id is one slot | Synthetic per-share member ids (`core_adapter/mapping/shares.py`) |
| 9.2 | Members | Closed three-value role enum; no responsibilities or separation-of-duties rule (design-time) | Planned: separate duty table in Kolo |
| 10 | Cross-cutting | No bridge between classic rotation and investments: no contribution split, no issuance derived from a contribution, no missed-contribution or exit rule | Treasurer retypes amount and unit price; contribution linked only by free-text `source_event` |
