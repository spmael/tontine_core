---
id: ADR-006
status: accepted
date: 2026-10-18
---

# ADR-006: Hybrid Contribution Allocation, Arrears, and Member Exit

## Context

`CAP-HYB-001` connects one recorded contribution to both a rotation pot and an
investment fund. The open choices in decision 8 of the
[next-version gap architecture](../next-version-gap-architecture.md) were which
amount is split, how late and missed contributions affect units, and how units
are settled when a member leaves.

The choices were reviewed by a practitioner who advises Cameroonian tontines and
njangi, a fund accountant specialising in unit pricing, a CEMAC/OHADA governance
and compliance expert, and a ledger architect. They agreed on the three main
questions. The project owner settled four points they disagreed on: exit
valuation, exit fee, penalty order, and catch-up of a missed fund share.

Amended 2026-10-18 after research by an IFRS/SYSCOHADA accountant and an OHADA
and Cameroonian law researcher on unit classification, repayment deferral,
heirs, and expulsion. Their findings changed the fee, deferral, and heir rules.

## Decision

### Invariants

- Units are issued only from a recorded contribution.
- A contribution produces at most one allocation, keyed by `contribution_id`.
- Hybrid rule versions are immutable. A new version takes effect only from a
  future cycle and is never retroactive.
- Each allocation stores everything needed to replay it without resolving
  anything again: the rule versions, the valuation reference, the unit price,
  the pot and fund amounts, the units issued, and the cash residual.
- Corrections are new offsetting events linked to the original. Nothing is
  edited.
- The settlement position is a pure calculation over recorded history and is
  never stored.
- Persistence adapters must enforce the one-allocation-per-contribution key, for
  example with a unique database constraint. The core defines the allocation
  repository protocol and shared contract tests that every adapter, including
  the Kolo adapter, must pass, and enforces the key in memory.
- Allocation, reversal, election, arrears, and exit events emit canonical audit
  events.

### Versioned hybrid rules

One immutable, versioned rule set per group is resolved by effective cycle, like
rotation versions. It holds:

- the fund share in basis points (`0..10_000`);
- the partial-payment order (see below);
- the catch-up policy for a missed fund share;
- the exit-fee schedule;
- the launch unit price used while no units are outstanding, for example
  1,000 XAF per unit;
- the maximum valuation age for issuing units;
- the payout deferral (see Member exit);
- the group's declared legal form (`association`, `cooperative`, or
  `unregistered`) and statute flags: an unconditional right to refuse
  redemption, pro-rata distribution on wind-up, and one fee schedule for all
  units.

Each version may cite the governance decision that adopted it.

### Split on the amount received

- The split applies to the amount actually received. The expected amount only
  measures arrears (expected minus received). Arrears are reported, never
  posted.
- Crediting units on the amount due and booking a member debt is not supported:
  it issues units nobody paid for and dilutes other members.
- `fund = round_down(received * bps / 10_000)` to the currency's smallest ISO
  4217 unit, and `pot = received - fund`. Pot plus fund always equals the amount
  received. This is an explicit, rule-governed posting rounding under ADR-001.
  Hybrid rules require a currency with an ISO minor unit.
- Units are `fund / unit price`, rounded down to 4 decimal places. The residual
  `fund - units * price` stays in the fund as cash and is stored on the
  allocation, so no value is lost.

### Partial payments and penalties

The partial-payment order is a closed, versioned choice. Each allocation records
the version it used.

- Penalty position: `penalty_first` (default), `penalty_last`, or `pro_rata`.
- Contribution position: `pot_first` (default) or `pro_rata`. Fund-first is not
  supported, because a beneficiary is waiting on the pot.

The penalty destination comes from the effective contribution rule, as required
by `FR-CON-007`. A `ROTATION_POT` destination is added so hybrid groups can
follow the usual bylaw of paying penalties into the pot. The default destination
of existing contribution rules does not change.

Waiving a penalty requires an approved governance decision. The member
concerned is excluded from that decision's electorate.

### Pricing

- A contribution paid on time or late, and a catch-up payment, issues units at
  the latest valuation in force on the date the money is received. Units are
  never backdated to the due date or to the missed cycle.
- If no valuation is in force, or it is older than the maximum age, the fund
  share is held as **pending allocation** until the next valuation. The price is
  never guessed. While no units are outstanding, the launch price applies.
- Exits use **forward pricing**: the first valuation dated on or after the exit
  date. Until that valuation exists the exit stays **pending valuation**.
- Catch-up timing is limited by the group's deadline and default forfeit rather
  than by forward pricing, as the owner decided.

### Missed contributions and catch-up

- A missed contribution issues no units. When the cycle closes unpaid, it
  becomes an explicit arrears event.
- The group decides, in the versioned rule, whether catch-up is allowed and the
  deadline in cycles. The default is allowed until the end of the next cycle.
- Within the deadline, the member records an explicit election: catch up at
  the valuation in force when the member pays, or forfeit that cycle's fund
  share.
- No election by the deadline applies the group default, which is `forfeit`.
- Forfeiting ends the fund arrears for that cycle only. It never cancels rotation
  arrears.

### Collateral

A member who owes rotation arrears cannot redeem units. Arrears may be offset
against units only through an explicit offset event, never silently.

### Member exit

- Every exit (voluntary, expulsion, or death) requires an approved governance
  decision and produces a recorded exit event. The exiting member is excluded
  from an expulsion decision's electorate.
- From the exit date, the member's units are frozen and no new units are issued.
  The exit is priced at the first valuation on or after the exit date and stays
  **pending valuation** until it exists.
- Settlement lines, in order: gross unit value, exit fee, unpaid dues and
  penalties, then pot received in excess of the member's contributions. A
  positive net is an entitlement owed to the member. A negative net is reported
  as an amount the member owes and is never hidden.
- Exit dues are set off against the gross value remaining after the fee, using
  oldest arrears cycle first and then penalty, rotation-pot, and fund amounts.
  The offset is an append-only event; any debt above the available value
  remains unpaid. The order follows the default penalty-first policy and is not
  independently configurable.
- Exit settlement uses the existing recorded contribution cycles and classic
  payout events through the exit date to derive excess pot received; callers do
  not supply an untraceable total. Monetary settlement lines are rounded to the
  currency's smallest ISO unit using half-even rounding.
- The payout is recorded as an entitlement and executed outside the library. By
  default it is deferred to the end of the cycle. A configured liquidity cap
  produces a first-come queue report when the fund cannot pay everyone at once.
- Deferral is capped: at most 12 months after the exit takes effect by default,
  and never more than 24 months. Going beyond 12 months needs an approved
  governance decision that records its reason. This follows AUSCOOP art. 11
  for cooperatives; for associations the bylaws govern within the same cap.
- Payout statuses: `pending_valuation`, `queued`, `payable`, `held_for_estate`,
  `consigned` (deposited or under judicial sequestration, with a reference), and
  `paid_externally` (with a reference).
- Debts owed by the exiting member remain due and are set off explicitly, under
  the Civil Code and the bylaws.
- Silent confiscation and automatic redistribution of units are not supported.

### Exit fee

- The fee is a percentage of gross unit value, set per exit type in the
  versioned rule. The default is 0.
- Any fee goes to the fund, to compensate the members who stay. It never goes to
  the treasurer or operator.
- One fee schedule applies to every unit, whatever its age, so all units keep
  identical terms (IAS 32 para 16A). Fees may still differ by exit type.
- A fee change takes effect only from a future cycle and must be adopted at
  least one full cycle before it applies. This is the notice period. An exit
  requested before the new version's effective cycle is charged the previous
  fee, so a member who objects can leave on the old terms.
- The expulsion fee may not exceed the voluntary-exit fee. This is enforced when
  the declared legal form is `cooperative` (AUSCOOP art. 15: an expelled member
  is refunded on the same terms) and is a warning otherwise. Forfeiture of units
  on expulsion is not supported.
- Death is fixed at 0 and cannot be configured.

### Death

- No penalty and no exit fee.
- The entitlement is held for the estate until a proof-of-succession reference is
  recorded. In Cameroon this is usually a *jugement d'hérédité*; the library
  stores the reference and does not judge it.
- If the heirs' claim is disputed, the entitlement is not held indefinitely. It
  moves to `consigned` with a reference to the deposit (*consignation*, Civil
  Code art. 1257 and following) or the court-appointed sequestrator.
- An heir can take over the seat only through a governance vote. Seat transfer
  belongs to `CAP-MEM-001` and is not built by this capability.

### Classification of units

Resolved for the domain on 2026-10-18 after research by an IFRS/SYSCOHADA
accountant and an OHADA and Cameroonian law researcher. This is research, not
legal advice.

- IFRS is mandatory only for listed or public-savings entities. Declared
  associations use SYCEBNL (in force 1 January 2024), cooperatives likely use
  SYSCOHADA or its cash-based SMT, and unregistered tontines have no mandatory
  framework.
- Tested under IAS 32, redeemable units are a liability by default. The equity
  exception (paras 16A-16B) needs statutes drafted for it. A liquidity cap or
  deferral does not make units equity; under IFRIC 2 only an unconditional right
  to refuse redemption does, which would contradict the guaranteed exit.
- The rotating pot is a separate obligation to the next beneficiary and ranks
  ahead of units.
- The domain stays neutral. It records units, NAV per valuation, redemption
  requests (fixing valuation, fee, offsets, net payable, queue position,
  status), a separate pot position, and the statute flags. Reporting presents
  units as "member funds: redeemable" with a liability flag by default. A local
  chartered accountant (expert-comptable, ONECCA) confirms the final treatment.

## Alternatives Considered

- **Split on the amount due**: rejected because it issues unpaid units and
  dilutes members who paid.
- **Backdate late units to the due-date valuation**: rejected because a late
  payer could choose the cheaper price.
- **Latest valuation at exit**: rejected in favour of forward pricing, so a
  member cannot exit at a price already known.
- **Exit fee 5-20% by default**: rejected; groups may set one, but a default fee
  would penalise members whose bylaws set none.
- **Free-form payment allocation**: rejected in favour of a closed, versioned
  list, so disputes can be answered from the record.
- **Catch-up chosen freely at any time**: rejected because members could skip
  the fund when prices are high and catch up when they fall.
- **Always forfeit a missed fund share**: rejected because groups commonly allow
  catch-up; the group sets the rule.
- **Fee in force when the member joined**: rejected because units of different
  ages would carry different terms, failing the IAS 32 identical-features test.
  Notice plus exit on the old terms protects members instead.
- **Forfeiture or a 5-20% penalty on expulsion**: rejected; AUSCOOP art. 15
  refunds an expelled cooperative member on the same terms as a voluntary exit.
- **Hard-code units as equity or as a liability**: rejected; classification
  depends on statutes and the applicable accounting framework, so the domain
  stores facts and statute flags and reporting derives the presentation.

## Consequences

### Positive

- Units always trace to money actually received, at a recorded price.
- Replaying history never re-resolves a rule or price.
- Late, missed, catch-up, and exit outcomes are explicit events visible to
  members.

### Negative or Trade-offs

- Contributions and exits can sit pending until a fresh valuation is recorded.
- Governance needs typed exit, waiver, and deferral effects with
  interested-member recusal.
- Contribution penalties gain a `ROTATION_POT` destination.
- Legal limits are encoded only where research found a clear rule (cooperative
  expulsion fee, 24-month deferral); other forms rely on bylaws and warnings.

## Open Questions

- Final presentation of units, confirmed by an ONECCA chartered accountant.
- Admission of heirs to a seat in cooperatives with a board; the researcher
  found the rule only for the simplified cooperative (AUSCOOP art. 221).
- Whether a penalty clause in the bylaws is binding as written under the
  pre-1960 French Civil Code still applied in Cameroon (unconfirmed).

## Sources

Named by the researchers: IAS 32 and IFRIC 2 (IFRS Foundation), SYCEBNL and
AUDCIF (ohada.com, ohada.org), AUSCOOP (FAO Faolex), Law 90/053 (bvm-ac.org),
and Ohadata J-12-250 on the *jugement d'hérédité*.

## Verification

- A Hypothesis property test shows pot plus fund equals the amount received for
  any basis-point value and any valid XAF or EUR amount, alongside explicit
  boundary examples.
- Shared repository contract tests reject a second allocation for the same
  `contribution_id` in every repository implementation.
- Tests cover duplicate allocation, non-retroactive versions, pending allocation
  and pending exit valuation, catch-up at the valuation in force on payment,
  forward exit pricing, partial-payment orders,
  catch-up elections and default forfeit, collateral, exit offsets and negative
  nets, death at zero fee, and reversal events.
- Tests cover fee notice and exit on old terms, the cooperative expulsion-fee
  limit, the 12- and 24-month deferral limits, consignment of disputed heir
  claims, and the default redeemable-liability presentation.
- Traceability links this decision to `CAP-HYB-001` and its tasks.
