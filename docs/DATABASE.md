# Database Design

This document defines the SQLite schema for the MVP and the JSON shape that will be stored for each user's single Kanban board.

## Goals

- Keep the database simple
- Support multiple users in the schema, even though MVP auth is hardcoded
- Store one board per user in the MVP
- Store the board itself as a JSON blob in SQLite
- Keep the stored shape close to the current frontend model

## SQLite Tables

### `users`

Purpose:

- Represents an application user
- Supports future expansion beyond the single hardcoded MVP user

Proposed schema:

```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Notes:

- For the MVP, the backend can seed one row for `user`
- Authentication is still hardcoded in Phase 4; this table exists so the database model is ready for future real user storage

### `boards`

Purpose:

- Stores the single Kanban board for a given user
- Keeps board state in a single JSON text column

Proposed schema:

```sql
CREATE TABLE boards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  board_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

Notes:

- `UNIQUE (user_id)` enforces the MVP rule of one board per user
- `board_json` stores the entire board as JSON text
- `updated_at` should be refreshed whenever the board is written

## Stored Board JSON

The stored JSON should use a minimal envelope:

```json
{
  "columns": [
    {
      "id": "backlog",
      "title": "Backlog",
      "cards": [
        {
          "id": "card-1",
          "title": "Customer interview notes",
          "details": "Summarize top pain points from three onboarding calls."
        }
      ]
    }
  ]
}
```

## JSON Shape

### Top level

- `columns`: array of column objects

### Column

- `id`: stable string identifier such as `backlog` or `done`
- `title`: user-editable column title
- `cards`: ordered array of cards in that column

### Card

- `id`: stable string identifier such as `card-1`
- `title`: card title
- `details`: card details text

## Why Use a JSON Blob

- The frontend already works with board-shaped nested data
- The MVP only needs one board per user
- Reads and writes stay simple in Phase 6
- This avoids unnecessary relational modeling before it is needed

## Tradeoffs

Accepted for the MVP:

- Partial updates are harder than in a fully relational schema
- Querying individual cards in SQL is not the focus
- Validation must happen in application code before writes

Still acceptable because:

- The board is small
- The app is local-only
- The MVP prioritizes simplicity over query flexibility

## Default Seed Data

When a board is first created for the MVP user, `board_json` should contain the current default board shape from the frontend:

- `backlog`
- `todo`
- `in-progress`
- `review`
- `done`

This keeps backend initialization aligned with the existing Kanban demo.

## Future Evolution

If the app later supports multiple boards per user:

- Remove the `UNIQUE` constraint on `boards.user_id`
- Add board-level metadata such as `name` and `position`
- Keep `board_json` for MVP continuity unless a clear need appears for relational card tables
