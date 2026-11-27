# Parallel Change (Expand-Contract) Checklist: <API / Schema / Column Name>

Use this four-phase protocol (Fowler Ch. 2.5) whenever renaming, splitting, or restructuring a **published API**, **serialized wire/event payload**, **shared configuration**, or **database column/table** where callers and writers cannot be updated atomically in a single commit or deployment.

## Target Contract Change

- **Old Representation**: `<e.g., column customer_name / JSON field userName / fn circum(r)>`
- **New Representation**: `<e.g., columns given_name + family_name / JSON field fullName / fn circumference(r)>`
- **Consumers / Readers Inventory**:
  - `<service / module / external client list>`
- **Producers / Writers Inventory**:
  - `<service / module / migration job list>`

## Phase 1: Expand (Additive Only - Zero Breaking Change)

- [ ] Add the new column (nullable/defaulted), JSON property, or new function (`circumference`) alongside the existing one.
- [ ] Keep the old representation intact and authoritative.
- [ ] Deploy/commit and verify existing tests and consumers remain green.

## Phase 2: Dual-Write & Backfill

- [ ] Update all write paths / setters to populate **both** the old and new representations atomically.
- [ ] Add an assertion or metric comparing derived/read equivalence where applicable (`10.6 Introduce Assertion` in non-prod or shadow reads).
- [ ] Run an idempotent backfill script/migration to populate historical records still missing the new representation.
- [ ] Verify zero null/missing mismatches across existing records.

## Phase 3: Migrate Readers Incrementally

- [ ] Switch internal readers one module/caller at a time to read from the new representation (falling back to old only if backfill is still in flight).
- [ ] For published functions/APIs, mark the old declaration `@deprecated` and forward it to the new declaration (`6.5 Change Function Declaration - Migration Mechanics`).
- [ ] Monitor logs/metrics to confirm zero remaining reads/calls against the old representation over a full traffic window.

## Phase 4: Contract (Clean Up)

- [ ] Remove dual-write logic so writers only write to the new representation.
- [ ] Confirm rollback safety window has passed with zero errors.
- [ ] Drop the obsolete column, JSON field, or deprecated forwarding wrapper (`8.9 Remove Dead Code`).
- [ ] Run full test and contract verification suite.
