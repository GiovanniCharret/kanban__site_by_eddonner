from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
FRONTEND_DIR = BASE_DIR.parent / "frontend" / "out"
SESSION_COOKIE = "kanban_session"
VALID_USERNAME = "user"
VALID_PASSWORD = "password"

app = FastAPI(title="Kanban MVP Backend")


class LoginRequest(BaseModel):
    username: str
    password: str


def is_authenticated(request: Request) -> bool:
    return request.cookies.get(SESSION_COOKIE) == VALID_USERNAME


@app.get("/api/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/session")
async def session(request: Request) -> dict[str, bool | str]:
    if is_authenticated(request):
        return {"authenticated": True, "username": VALID_USERNAME}

    return {"authenticated": False}


@app.post("/api/login")
async def login(payload: LoginRequest, response: Response) -> dict[str, bool | str]:
    if payload.username != VALID_USERNAME or payload.password != VALID_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    response.set_cookie(
        key=SESSION_COOKIE,
        value=VALID_USERNAME,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return {"authenticated": True, "username": VALID_USERNAME}


@app.post("/api/logout")
async def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(key=SESSION_COOKIE, path="/")
    return {"authenticated": False}


@app.get("/")
async def root() -> FileResponse:
    if FRONTEND_DIR.exists():
        return FileResponse(FRONTEND_DIR / "index.html")

    return FileResponse(STATIC_DIR / "index.html")


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
