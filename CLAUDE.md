# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A local Kanban board app with an AI chat sidebar. Single Docker container: Next.js static frontend served by a FastAPI backend, SQLite for persistence, OpenRouter for AI.

**Auth**: hardcoded `user` / `password` (MVP only, intentional).

## Commands

### Backend

```bash
cd backend
# Install (requires uv or pip)
uv pip install -e ".[dev]"

# Run dev server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest
pytest tests/test_auth.py          # single file
pytest -k "test_login"             # single test
```

### Frontend

```bash
cd frontend
npm install

npm run dev          # dev server on :3000
npm run build        # static export → out/
npm run lint
npm test             # vitest unit tests (with coverage)
npm run test:watch   # vitest in watch mode
npm run test:e2e     # playwright e2e (requires running server)
```

### Docker (full stack)

```bash
# Windows
scripts/start-server.ps1
scripts/stop-server.ps1

# macOS/Linux
scripts/start-server.sh
scripts/stop-server.sh
```

The start scripts build the image and run the container, mounting `./data` to persist the SQLite DB. App runs on port 8000.

## Architecture

```
frontend/src/
  app/page.tsx          → entry, renders AppShell
  components/
    AppShell.tsx        → layout: KanbanBoard + chat sidebar
    KanbanBoard.tsx     → drag-drop board (dnd-kit), inline card editing
  lib/kanban.ts         → board types + pure state operations

backend/app/
  main.py               → FastAPI routes: /api/auth/*, /api/board, /api/chat
  board.py              → Pydantic models: BoardModel, ColumnModel, CardModel
  db.py                 → SQLite init, user/board CRUD
  ai.py                 → OpenRouter HTTP client (DNS-over-HTTPS fallback)
  ai_board.py           → system prompt, operation parsing, board mutation
```

**Data flow for AI chat**: user message → `ai_board.py` builds prompt (board JSON + chat history) → OpenRouter (`openai/gpt-oss-120b`, temp 0.2, max 800 tokens) → response parsed for structured operations (`create_card`, `update_card`, `move_card`, `delete_card`, `rename_column`) → applied to board → saved to SQLite.

**Board storage**: one board per user, stored as a JSON blob in `boards.board_json`. The SQLite schema is in `docs/DATABASE.md`.

**Frontend build**: Next.js exports static files to `frontend/out/`. In Docker, FastAPI mounts and serves these at `/`; API routes live at `/api/*`.

## Key Constraints (MVP Scope)

- One board per user, five fixed columns
- No multiple boards, no archiving, no filtering
- No real auth — session cookie `kanban_session` set on login
- OpenRouter API key required in `.env` as `OPENROUTER_API_KEY`

## Color Tokens

| Role | Value |
|------|-------|
| Accent Yellow | `#ecad0a` |
| Blue Primary | `#209dd7` |
| Purple Secondary | `#753991` |
| Dark Navy | `#032147` |
| Gray Text | `#888888` |

## Docs

- `docs/DATABASE.md` — SQLite schema and board JSON shape
- `docs/AI.md` — OpenRouter config and DNS fallback details
- `docs/PLAN.md` — 10-phase delivery plan (mostly complete)
