# Project Delivery Plan

This document is the execution plan for the local MVP. The scope is intentionally narrow:

- Next.js frontend
- FastAPI backend
- FastAPI serves the statically built frontend at `/`
- SQLite stores one JSON board blob per user
- MVP auth uses hardcoded credentials: `user` / `password`
- AI uses OpenRouter with `openai/gpt-oss-120b`
- AI board changes are returned as structured operations, not full board replacements
- Integration testing should stay primarily at the API layer
- Aim for roughly 80% test coverage when it is sensible, but do not add low-value tests just to hit a target

## Phase 1: Planning and Documentation

Success criteria:

- This plan reflects the approved MVP scope and technical decisions
- Encoding issues and unclear wording are corrected
- `frontend/AGENTS.md` documents the current frontend-only MVP accurately
- The repo has a clear baseline for the next implementation phases

Checklist:

- [x] Rewrite `docs/PLAN.md` into a detailed execution plan
- [x] Record the approved decisions from the user
- [x] Keep the scope constrained to the MVP
- [x] Create `frontend/AGENTS.md` describing the current frontend state

## Phase 2: Backend and Container Scaffolding

Success criteria:

- `backend/` contains a minimal FastAPI application
- The app serves a simple API route and a simple HTML response before frontend integration
- Docker builds and runs the app locally
- Python dependencies are managed with `uv` inside the container
- `scripts/` contains start/stop scripts for Windows, macOS, and Linux

Checklist:

- [x] Create FastAPI app structure in `backend/`
- [x] Add dependency and environment configuration for Python backend work
- [x] Add a health route such as `GET /api/health`
- [x] Add a temporary hello-world route or page to prove backend serving works
- [x] Create a Dockerfile for the combined app
- [x] Add a `.dockerignore`
- [x] Create cross-platform start scripts in `scripts/`
- [x] Create cross-platform stop scripts in `scripts/`
- [x] Verify the container starts locally and the API responds

## Phase 3: Static Frontend Serving

Success criteria:

- The existing Next.js app builds as static assets
- FastAPI serves the built frontend at `/`
- The current Kanban demo appears from the backend-served app
- Existing frontend unit and browser tests are updated only as needed

Checklist:

- [x] Confirm the current frontend can be exported as static output
- [x] Adjust the Next.js config if required for static export
- [x] Add a build flow that outputs static frontend assets for backend serving
- [x] Wire FastAPI to serve the generated frontend files
- [x] Verify `/` serves the Kanban demo through FastAPI
- [x] Keep the frontend-only MVP behavior unchanged at this stage

## Phase 4: Dummy Sign-In Flow

Success criteria:

- Visiting `/` requires sign-in before the board is shown
- Only `user` / `password` is accepted
- Sign-in state survives normal navigation for the running app session
- The user can log out and return to the sign-in screen
- Frontend and API tests cover the sign-in flow

Checklist:

- [x] Choose the simplest backend-backed session approach compatible with static frontend serving
- [x] Add login and logout API routes
- [x] Add minimal frontend login UI
- [x] Hide the board until authentication succeeds
- [x] Add logout UI
- [x] Add frontend tests for login/logout rendering and behavior
- [x] Add API integration tests for login/logout

## Phase 5: Database Design

Success criteria:

- The SQLite approach is documented in `docs/`
- The persisted board format is defined clearly
- One user maps to one board record in the MVP
- Board state is stored as a JSON blob in SQLite
- The user can review the schema and storage approach before implementation continues

Checklist:

- [x] Define the SQLite schema for users and boards
- [x] Store board state as JSON text in the board record
- [x] Document the schema and persistence approach in `docs/`
- [x] Include a representative JSON example for the board blob
- [x] Include notes on how this can evolve to multiple boards later
- [ ] Get user sign-off on the schema document

## Phase 6: Backend Kanban API

Success criteria:

- The database is created automatically if it does not exist
- The backend can read the signed-in user's board
- The backend can replace or update the signed-in user's board safely
- Backend unit tests cover schema, persistence, and API behavior
- API integration tests validate the main board flows

Checklist:

- [x] Add SQLite initialization on startup
- [x] Seed or create the MVP user record as needed
- [x] Seed or create a default board for the MVP user
- [x] Add `GET` route to fetch the current user's board
- [x] Add write route(s) to persist board changes for the current user
- [x] Validate incoming board payloads
- [x] Add backend unit tests for database and service logic
- [x] Add API integration tests for board fetch and update flows

## Phase 7: Frontend and Backend Integration

Success criteria:

- The frontend no longer uses only in-memory board state
- On load, the board is fetched from the backend after authentication
- Column rename, card create, card delete, and drag/drop persist through the API
- Refreshing the app preserves board changes
- API-focused integration tests cover persistence behavior

Checklist:

- [ ] Add a frontend API client layer for auth and board requests
- [ ] Load the board from the backend after login
- [ ] Persist column rename changes
- [ ] Persist card creation changes
- [ ] Persist card deletion changes
- [ ] Persist drag/drop changes
- [ ] Handle loading and error states simply
- [ ] Update frontend tests for backend-backed behavior
- [ ] Add API integration tests for end-to-end persistence paths

## Phase 8: AI Connectivity

Success criteria:

- The backend can call OpenRouter using `OPENROUTER_API_KEY`
- The model used is `openai/gpt-oss-120b`
- A simple backend test route or service call proves AI connectivity with a `2 + 2` prompt
- Failures are surfaced clearly without over-engineering

Checklist:

- [ ] Add backend settings for OpenRouter configuration
- [ ] Implement a small OpenRouter client in the backend
- [ ] Add a simple connectivity test path or service-level test harness
- [ ] Verify a minimal prompt/response flow works locally
- [ ] Document required environment variables briefly

## Phase 9: AI Board Context and Structured Outputs

Success criteria:

- AI requests include the board JSON, the user message, and conversation history
- AI responses are parsed into a structured format
- Board mutations are expressed as operations, not free-form text
- Backend validation prevents invalid operations from corrupting saved state
- Tests cover operation parsing and application

Checklist:

- [ ] Define the structured AI response schema
- [ ] Define the supported operation types
- [ ] Implement backend prompt construction with board state and chat history
- [ ] Parse and validate model outputs
- [ ] Apply valid operations to the stored board
- [ ] Return both assistant text and applied changes to the frontend
- [ ] Add unit tests for operation validation and application
- [ ] Add API integration tests for AI-assisted board updates

Suggested operation set:

- `create_card`
- `update_card`
- `move_card`
- `delete_card`
- `rename_column`

## Phase 10: AI Chat Sidebar UI

Success criteria:

- The frontend includes a sidebar chat UI
- The user can send messages and view conversation history
- AI responses are displayed alongside any applied board changes
- If the AI updates the board, the UI refreshes automatically
- The design stays aligned with the existing visual direction

Checklist:

- [ ] Design and build a sidebar chat layout within the existing app shell
- [ ] Add frontend state for chat history and request lifecycle
- [ ] Send board-aware chat requests to the backend
- [ ] Render assistant responses clearly
- [ ] Refresh or reconcile board state after successful AI operations
- [ ] Add frontend tests for chat UI behavior
- [ ] Add API integration coverage for chat-triggered board updates

## Guardrails

- Keep the implementation simple and local-first
- Do not add extra auth providers, multi-board UX, or multi-user UI in the MVP
- Prefer small service layers and explicit data shapes over abstraction
- Prioritize valuable tests; approximate 80% coverage is a goal, not a reason to add unnecessary tests
- Root-cause issues before changing code
- Keep documentation concise and current as phases complete
