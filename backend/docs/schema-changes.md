# Schema Changes

## Phase 2.5: Add tokens column to threads table

Added `tokens` integer column to store token usage from LLM classification calls.

```sql
ALTER TABLE threads ADD COLUMN tokens TEXT DEFAULT '0';
```

Applied: SQLite (auto-migrated via ORM)

## Phase 3.3: Add instruction and warnings columns to drafts table

Added columns for draft generation tracking:
- `instruction` TEXT: the user's instruction for the draft
- `warnings` TEXT: JSON-encoded list of validation warnings

```sql
ALTER TABLE drafts ADD COLUMN instruction TEXT;
ALTER TABLE drafts ADD COLUMN warnings TEXT;
```

Applied: SQLite (auto-migrated via ORM)
