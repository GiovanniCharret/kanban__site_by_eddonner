import json
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from app.board import BoardModel, CardModel


SUPPORTED_OPERATION_TYPES = (
    "create_card",
    "update_card",
    "move_card",
    "delete_card",
    "rename_column",
)


class AIBoardError(RuntimeError):
    pass


class ChatMessageModel(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class BoardOperationModel(BaseModel):
    type: Literal["create_card", "update_card", "move_card", "delete_card", "rename_column"]
    column_id: str | None = None
    card_id: str | None = None
    title: str | None = None
    details: str | None = None
    target_column_id: str | None = None
    target_index: int | None = None


class AIBoardResponseModel(BaseModel):
    assistant_message: str
    operations: list[BoardOperationModel] = Field(default_factory=list)


class AIChatRequest(BaseModel):
    message: str = Field(..., max_length=2000)
    history: list[ChatMessageModel] = Field(default_factory=list, max_length=50)


class AIChatResponse(BaseModel):
    assistant_message: str
    operations: list[BoardOperationModel]
    board: BoardModel


def build_board_ai_prompt(board: BoardModel, message: str, history: list[ChatMessageModel]) -> str:
    history_lines = []
    for item in history:
        history_lines.append(f"{item.role}: {item.content}")

    conversation_history = "\n".join(history_lines) if history_lines else "(no prior messages)"
    operation_list = ", ".join(SUPPORTED_OPERATION_TYPES)

    return f"""You are helping manage a kanban board.

Return only valid JSON.
Do not include markdown fences.
Do not return any text before or after the JSON object.

Allowed operation types: {operation_list}

Rules:
- Use operations only when a board change is needed.
- Keep operations minimal.
- Never invent columns or cards without including the required ids and values.
- If no board change is needed, return an empty operations array.

Response JSON shape:
{{
  "assistant_message": "short helpful reply",
  "operations": [
    {{
      "type": "create_card" | "update_card" | "move_card" | "delete_card" | "rename_column",
      "column_id": "required for create_card and rename_column",
      "card_id": "required for card operations",
      "title": "required for create_card, rename_column, and optional for update_card",
      "details": "required for create_card and optional for update_card",
      "target_column_id": "required for move_card",
      "target_index": "optional for move_card"
    }}
  ]
}}

Board JSON:
{json.dumps(board.model_dump())}

Conversation history:
{conversation_history}

Latest user message:
{message}
"""


def parse_board_ai_response(response_text: str) -> AIBoardResponseModel:
    candidate = response_text.strip()
    if candidate.startswith("```"):
        lines = [line for line in candidate.splitlines() if not line.strip().startswith("```")]
        candidate = "\n".join(lines).strip()

    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise AIBoardError("Invalid AI response") from exc

    try:
        return AIBoardResponseModel.model_validate(data)
    except ValidationError as exc:
        raise AIBoardError(f"Invalid AI response structure: {exc.error_count()} validation errors") from exc
    except Exception as exc:
        raise AIBoardError(f"Unexpected parsing error: {type(exc).__name__}") from exc


def apply_board_operations(board: BoardModel, operations: list[BoardOperationModel]) -> BoardModel:
    # Operations are applied to a deep copy; the original board and database are only
    # updated after all operations succeed. If any operation raises AIBoardError,
    # the copy is discarded and the stored board is left untouched.
    updated_board = board.model_copy(deep=True)

    for operation in operations:
        if operation.type == "create_card":
            _apply_create_card(updated_board, operation)
        elif operation.type == "update_card":
            _apply_update_card(updated_board, operation)
        elif operation.type == "move_card":
            _apply_move_card(updated_board, operation)
        elif operation.type == "delete_card":
            _apply_delete_card(updated_board, operation)
        elif operation.type == "rename_column":
            _apply_rename_column(updated_board, operation)
        else:
            raise AIBoardError("Invalid AI operation")

    return updated_board


def _apply_create_card(board: BoardModel, operation: BoardOperationModel) -> None:
    if not operation.column_id or not operation.card_id or not operation.title or operation.details is None:
        raise AIBoardError("Invalid AI operation")

    if _has_card(board, operation.card_id):
        raise AIBoardError("Invalid AI operation")

    column = _find_column(board, operation.column_id)
    column.cards.append(
        CardModel(
            id=operation.card_id,
            title=operation.title,
            details=operation.details,
        )
    )


def _apply_update_card(board: BoardModel, operation: BoardOperationModel) -> None:
    if not operation.card_id or (operation.title is None and operation.details is None):
        raise AIBoardError("Invalid AI operation")

    _, card = _find_card(board, operation.card_id)
    if operation.title is not None:
        card.title = operation.title
    if operation.details is not None:
        card.details = operation.details


def _apply_move_card(board: BoardModel, operation: BoardOperationModel) -> None:
    if not operation.card_id or not operation.target_column_id:
        raise AIBoardError("Invalid AI operation")

    source_column, card = _find_card(board, operation.card_id)
    target_column = _find_column(board, operation.target_column_id)
    source_column.cards = [item for item in source_column.cards if item.id != operation.card_id]

    insert_index = len(target_column.cards) if operation.target_index is None else operation.target_index
    if insert_index < 0 or insert_index > len(target_column.cards):
        raise AIBoardError("Invalid AI operation")

    target_column.cards.insert(insert_index, card)


def _apply_delete_card(board: BoardModel, operation: BoardOperationModel) -> None:
    if not operation.card_id:
        raise AIBoardError("Invalid AI operation")

    column, _ = _find_card(board, operation.card_id)
    column.cards = [item for item in column.cards if item.id != operation.card_id]


def _apply_rename_column(board: BoardModel, operation: BoardOperationModel) -> None:
    if not operation.column_id or not operation.title:
        raise AIBoardError("Invalid AI operation")

    column = _find_column(board, operation.column_id)
    column.title = operation.title


def _find_column(board: BoardModel, column_id: str):
    for column in board.columns:
        if column.id == column_id:
            return column

    raise AIBoardError("Invalid AI operation")


def _find_card(board: BoardModel, card_id: str):
    for column in board.columns:
        for card in column.cards:
            if card.id == card_id:
                return column, card

    raise AIBoardError("Invalid AI operation")


def _has_card(board: BoardModel, card_id: str) -> bool:
    for column in board.columns:
        for card in column.cards:
            if card.id == card_id:
                return True

    return False
