---
id: ADR-003
status: accepted
date: 2026-09-12
---

# ADR-003: External FX Rate Boundary

## Context

Investment tontines may hold assets in currencies different from the group base
currency. Providers such as ECB can publish reference FX rates, but the core
package must remain framework-independent and must not perform network access,
market-data retrieval, scheduling, or provider-specific authentication.

## Decision

The investment core accepts provider-neutral, externally supplied FX-rate records.
Each rate must include:

- base currency;
- quote currency;
- Decimal rate;
- effective timestamp;
- provider/source identifier;
- source reference or publication metadata where available.

ECB may be implemented later as an adapter outside the domain core. The adapter
will fetch and translate ECB data into the provider-neutral rate record. The core
will validate and consume the supplied record but will not know about ECB URLs,
HTTP clients, credentials, retries, schedules, or provider response formats.

FX conversion must preserve source precision until an explicit posting or
settlement rounding policy is applied. Historical calculations must retain the
rate and source provenance used at the time.

## Alternatives Considered

- **Call ECB directly from investment entities**: rejected because it leaks
  network and provider concerns into the domain and makes tests nondeterministic.
- **Use a hard-coded FX table**: rejected because rates change and historical
  provenance would be lost.
- **Use one global FX rate**: rejected because rates are currency-pair and
  effective-time specific.

## Consequences

### Positive

- ECB and other providers can be swapped without changing investment entities.
- Tests use deterministic fixtures rather than live network calls.
- FX calculations remain auditable and reproducible.
- The V1 core preserves its no-market-data and no-external-access boundary.

### Negative or Trade-offs

- Callers or adapters must supply current and valid rates.
- Staleness and rate-selection policies must be explicit.
- A later adapter package is required for live ECB retrieval.

## Verification

- Investment vocabulary tests construct FX records without network access.
- Adapter contract tests use recorded provider fixtures.
- Boundary review rejects HTTP imports and live provider calls from the domain package.
