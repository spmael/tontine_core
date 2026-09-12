---
name: python-standards
description: >-
  Python standards for tontine-core. Use when writing or reviewing Python code,
  public APIs, financial calculations, tests, docstrings, or code comments.
user_invocable: false
---

# Python Standards

## Style

- Target Python 3.12+.
- Use type hints for public APIs and important domain values.
- Prefer small modules organized by domain capability.
- Keep runtime dependencies minimal and keep framework code at the boundary.
- Use `Decimal` for monetary values; never use binary floats for financial calculations.
- Use immutable value objects where practical and make state transitions explicit.

## Docstrings

Public classes, functions, methods, and modules should have concise Google-style
docstrings when their purpose is not obvious from their name and type hints.

Use only the sections that add information:

```python
def calculate_nav(assets: Decimal, liabilities: Decimal) -> Decimal:
    """Calculate net asset value in the tontine base currency.

    Args:
        assets: Total recorded assets in base-currency units.
        liabilities: Total recorded liabilities in base-currency units.

    Returns:
        Assets minus liabilities.
    """
```

Guidelines:

- Keep the summary to one clear sentence.
- Include `Args`, `Returns`, and `Raises` only when useful.
- State currency, amount units, precision, or rounding behavior for financial APIs.
- Explain the governing business rule or formula when it is not self-evident.
- Do not repeat the function name, type annotations, or implementation line by line.
- Private helpers usually need no docstring when their name and types are clear.

## Comments

Prefer clear names and structure over comments. Add a short comment only when it
explains why the code must do something non-obvious, such as a financial rule,
rounding decision, ordering constraint, or compatibility requirement.

- Keep comments short, usually one sentence.
- Place the comment immediately before the relevant code.
- Do not narrate assignments, branches, or obvious loops.
- Do not use comments as a substitute for a docstring or a design decision.
- Keep domain rationale in the nearest public docstring or an ADR when it is broader than one code block.

## Tests

- Test public behavior and domain invariants rather than implementation details.
- Include invalid transitions, duplicate events, negative values, rounding, and currency cases.
- Keep core tests runnable without a database, web framework, or network.
- Use descriptive test names that state the behavior under test.
