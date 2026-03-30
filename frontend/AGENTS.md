# Frontend Notes

This directory contains the current frontend-only MVP for the Kanban board. It is already functional as a standalone Next.js app and should be treated as the visual and interaction baseline for later backend integration.

## Current Stack

- Next.js app router
- React 19
- TypeScript
- Tailwind CSS v4 tooling, with most styling currently authored in `src/app/globals.css`
- `@dnd-kit` for drag and drop
- Vitest + Testing Library for unit/component tests
- Playwright for browser coverage

## Current Behavior

- The homepage renders a single `KanbanBoard` component from `src/components/KanbanBoard.tsx`
- There is one board with five fixed columns:
  - `backlog`
  - `todo`
  - `in-progress`
  - `review`
  - `done`
- Column titles are editable inline
- Cards can be created and deleted
- Cards can be dragged within and across columns
- Board data is currently in-memory only and initialized from `src/lib/kanban.ts`
- There is no authentication, backend integration, persistence, or AI UI yet

## Important Files

- `src/app/page.tsx`: app entry point
- `src/components/KanbanBoard.tsx`: main board UI and interaction wiring
- `src/lib/kanban.ts`: board types, seed data, and board state operations
- `src/lib/kanban.test.ts`: unit tests for board state logic
- `src/components/KanbanBoard.test.tsx`: component tests for core interactions
- `e2e/kanban.spec.ts`: Playwright smoke flow for the current board

## Constraints for Future Work

- Preserve the existing MVP behavior unless a phase explicitly changes it
- Keep the frontend compatible with static build output because FastAPI will serve the built assets
- Prefer simple client-side data fetching once backend APIs are introduced
- Keep integration testing primarily at the API level; do not expand browser E2E coverage without a specific reason
- Avoid adding frontend architecture that assumes multiple boards or real auth providers

## Testing Baseline

- `npm test` runs Vitest with coverage
- `npm run test:e2e` runs Playwright
- `npm run lint` runs ESLint

## Cleanup Notes

- This directory currently contains generated artifacts such as `.next/`, `coverage/`, `test-results/`, and `node_modules/`
- Treat those as build outputs, not source-of-truth project files
