import logging
import os
import secrets
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from time import monotonic

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.ai import OpenRouterError, run_openrouter_prompt
from app.ai_board import (
    AIBoardError,
    AIChatRequest,
    AIChatResponse,
    apply_board_operations,
    build_board_ai_prompt,
    parse_board_ai_response,
)
from app.board import BoardModel
from app.db import get_board_for_user, init_db, save_board_for_user

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
FRONTEND_DIR = BASE_DIR.parent / "frontend" / "out"
SESSION_COOKIE = "kanban_session"
VALID_USERNAME = os.environ.get("KANBAN_USERNAME", "user")
VALID_PASSWORD = os.environ.get("KANBAN_PASSWORD", "password")
# Set SECURE_COOKIES=true in production (HTTPS). Defaults to False for local HTTP dev.
SECURE_COOKIES = os.environ.get("SECURE_COOKIES", "false").lower() == "true"

# Server-side session store: token -> username
_sessions: dict[str, str] = {}

# Simple in-memory rate limiting for login
_login_attempts: dict[str, list[float]] = defaultdict(list)
_LOGIN_RATE_WINDOW = 60.0  # seconds
_LOGIN_RATE_MAX = 10       # max attempts per window per IP


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not os.environ.get("OPENROUTER_API_KEY"):
        logger.warning("OPENROUTER_API_KEY not set — AI features will return 500")
    init_db()
    yield


app = FastAPI(title="Kanban MVP Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


class LoginRequest(BaseModel):
    username: str
    password: str


def _check_login_rate_limit(client_ip: str) -> None:
    now = monotonic()
    window_start = now - _LOGIN_RATE_WINDOW
    attempts = [t for t in _login_attempts[client_ip] if t > window_start]
    if len(attempts) >= _LOGIN_RATE_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )
    _login_attempts[client_ip] = attempts + [now]


def is_authenticated(request: Request) -> bool:
    token = request.cookies.get(SESSION_COOKIE)
    return token is not None and token in _sessions


def require_authenticated_username(request: Request) -> str:
    token = request.cookies.get(SESSION_COOKIE)
    username = _sessions.get(token or "")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return username


@app.get("/api/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/session")
async def session(request: Request) -> dict[str, bool | str]:
    token = request.cookies.get(SESSION_COOKIE)
    if token and token in _sessions:
        return {"authenticated": True, "username": _sessions[token]}
    return {"authenticated": False}


class AiTestRequest(BaseModel):
    prompt: str = "What is 2 + 2?"


@app.post("/api/ai/test")
async def ai_test(request_data: AiTestRequest, request: Request) -> dict[str, object]:
    require_authenticated_username(request)
    try:
        result = run_openrouter_prompt(request_data.prompt, max_tokens=128)
    except OpenRouterError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return {
        "success": True,
        "prompt": request_data.prompt,
        "answer": result["response_text"],
    }


@app.post("/api/ai/chat", response_model=AIChatResponse)
async def ai_chat(request_data: AIChatRequest, request: Request) -> AIChatResponse:
    username = require_authenticated_username(request)
    board = get_board_for_user(username)
    prompt = build_board_ai_prompt(board, request_data.message, request_data.history)

    try:
        result = run_openrouter_prompt(prompt, max_tokens=800)
        parsed = parse_board_ai_response(result["response_text"])
        updated_board = apply_board_operations(board, parsed.operations)
    except OpenRouterError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except AIBoardError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    save_board_for_user(username, updated_board)
    return AIChatResponse(
        assistant_message=parsed.assistant_message,
        operations=parsed.operations,
        board=updated_board,
    )


@app.post("/api/login")
async def login(payload: LoginRequest, request: Request, response: Response) -> dict[str, bool | str]:
    client_ip = request.client.host if request.client else "unknown"
    _check_login_rate_limit(client_ip)

    if payload.username != VALID_USERNAME or payload.password != VALID_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = secrets.token_urlsafe(32)
    _sessions[token] = VALID_USERNAME
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        secure=SECURE_COOKIES,
        samesite="strict",
        path="/",
    )
    return {"authenticated": True, "username": VALID_USERNAME}


@app.post("/api/logout")
async def logout(request: Request, response: Response) -> dict[str, bool]:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        _sessions.pop(token, None)
    response.delete_cookie(key=SESSION_COOKIE, path="/")
    return {"authenticated": False}


@app.get("/api/board")
async def get_board(request: Request) -> BoardModel:
    username = require_authenticated_username(request)
    return get_board_for_user(username)


@app.put("/api/board")
async def update_board(board: BoardModel, request: Request) -> BoardModel:
    username = require_authenticated_username(request)
    save_board_for_user(username, board)
    return get_board_for_user(username)


@app.get("/")
async def root() -> FileResponse:
    if FRONTEND_DIR.exists():
        return FileResponse(FRONTEND_DIR / "index.html")

    return FileResponse(STATIC_DIR / "index.html")


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
