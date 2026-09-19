# Snowflake execution record

This is a non-production, controlled implementation benchmark. It records the
Snowflake-native path that was executed against an authorized Snowflake trial
account on 2026-09-19. It does not represent a customer deployment or customer
outcome.

## Objects exercised

- `LEKHASIGNAL` database with `RAW`, `CORE`, `MART`, and `CONTROL` schemas
- `LEKHASIGNAL_TRANSFORM_WH`: X-Small, auto-suspends after 60 seconds
- `RAW.PAYMENT_EVENTS_STREAM`: change stream over payment events
- `CONTROL.MERGE_PAYMENT_CDC`: triggered Task that keeps the newest event for
  each payment identifier
- `MART.FCT_REVENUE_RECOGNITION`: 15-minute Dynamic Table
- `CONTROL.REVENUE_RECONCILIATION`: operational reconciliation view

## Controlled test result

The seeded run intentionally inserted 500 invoice events, 500 payment events,
and 5 duplicate-payment test events. The resulting checks were:

| Check | Result |
|---|---:|
| Raw invoice events | 500 |
| Raw payment events | 505 |
| Canonical payment-ledger events | 500 |
| Revenue-mart rows after refresh | 500 |
| Duplicate payment identifiers detected | 5 |

The result demonstrates the designed behavior: duplicate source payment events
are visible in the raw layer and collapse to the latest source event in the
canonical ledger. It is a functionality benchmark, not a claim of financial
impact, model accuracy, customer DSO/CEI improvement, or production scale.

## Safe production boundary

The public Cloud Run console does not hold Snowflake credentials. A production
connection should use a dedicated least-privilege Snowflake service identity,
stored in Secret Manager, and only the repository's named read-only evidence
queries. The MCP server must continue to reject arbitrary agent-provided SQL.
