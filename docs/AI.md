# AI Configuration

Phase 8 uses OpenRouter from the backend.

Required environment variable:

- `OPENROUTER_API_KEY`: API key used by the backend for `openai/gpt-oss-120b`

Current connectivity check:

- `POST /api/ai/test`
- Requires login
- Sends the prompt to OpenRouter and returns a simple JSON response

Notes:

- The backend uses `https://openrouter.ai/api/v1/chat/completions`.
- The start scripts do not force Docker DNS by default.
- If your environment needs explicit DNS for containers, set `KANBAN_DOCKER_DNS` before starting:
  - PowerShell: `$env:KANBAN_DOCKER_DNS = "1.1.1.1,8.8.8.8"`
  - macOS/Linux: `export KANBAN_DOCKER_DNS="1.1.1.1,8.8.8.8"`
- If standard DNS resolution fails, the backend falls back to resolving `openrouter.ai` through DNS-over-HTTPS before retrying the request.
