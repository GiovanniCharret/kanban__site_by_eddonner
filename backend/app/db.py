import json
import os
import sqlite3
from pathlib import Path

from app.board import BoardModel, create_default_board


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "kanban.db"


def get_db_path() -> Path:
    configured = os.environ.get("KANBAN_DB_PATH")
    if configured:
        return Path(configured)

    return DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    default_board = create_default_board()

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS boards (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL UNIQUE,
              board_json TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO users (username)
            VALUES (?)
            """,
            ("user",),
        )

        user_row = connection.execute(
            """
            SELECT id
            FROM users
            WHERE username = ?
            """,
            ("user",),
        ).fetchone()

        if user_row is None:
            raise RuntimeError("Failed to seed MVP user")

        connection.execute(
            """
            INSERT OR IGNORE INTO boards (user_id, board_json)
            VALUES (?, ?)
            """,
            (
                user_row["id"],
                json.dumps(default_board.model_dump()),
            ),
        )
        connection.commit()


def get_board_for_user(username: str) -> BoardModel:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT boards.board_json
            FROM boards
            JOIN users ON users.id = boards.user_id
            WHERE users.username = ?
            """,
            (username,),
        ).fetchone()

    if row is None:
        raise RuntimeError(f"No board found for user '{username}'")

    return BoardModel.model_validate(json.loads(row["board_json"]))


def save_board_for_user(username: str, board: BoardModel) -> None:
    with get_connection() as connection:
        result = connection.execute(
            """
            UPDATE boards
            SET board_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = (
              SELECT id
              FROM users
              WHERE username = ?
            )
            """,
            (json.dumps(board.model_dump()), username),
        )
        connection.commit()

    if result.rowcount != 1:
        raise RuntimeError(f"Failed to save board for user '{username}'")
