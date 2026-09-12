# Ledger Domain Contract

The ledger contract is an internal domain contract. It is not a bank, payment,
or external API contract.

## Invariants

- Monetary amounts are finite, non-negative `Decimal` values.
- Every journal uses one explicit ISO 4217 currency.
- Every posted journal contains at least one debit and one credit.
- Total debits equal total credits before posting.
- Journal provenance includes an identifier, timezone-aware timestamp,
  description, and source event.
- Posted journals are immutable records.
- Account balances are derived from posted entries, not maintained balance fields.
- Corrections use reversal or adjustment entries and preserve original provenance.
- No journal operation initiates payment, accesses custody, retrieves live
  balances, or connects to an external institution.

## Precision Contract

- Intermediate calculations must not be quantized implicitly.
- Posting and settlement quantization requires an explicit business or legal
  policy.
- ISO currency precision is a default settlement/display quantum, not a global
  calculation precision or rounding mode.
- Rounding differences must remain attributable when they affect a posted event.

## Verification

The contract is verified by the ledger vocabulary, posting, and correction test
suites under `tests/ledger/`.
