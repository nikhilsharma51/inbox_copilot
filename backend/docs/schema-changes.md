# Schema Changes

## Phase 2.5: Add tokens column to threads table

Added `tokens` integer column to store token usage from LLM classification calls.

```sql
ALTER TABLE threads ADD COLUMN tokens TEXT DEFAULT '0';
```

Applied: SQLite (auto-migrated via ORM)
