# AI Configuration

Phase 8 uses OpenRouter from the backend.

Required environment variable:

- `OPENROUTER_API_KEY`: API key used by the backend for `openai/gpt-oss-120b`

Current connectivity check:

- `POST /api/ai/test`
- Requires login
- Sends the prompt to OpenRouter and returns a simple JSON response
