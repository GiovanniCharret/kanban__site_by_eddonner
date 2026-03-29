import pytest

from app.ai_board import (
    AIBoardError,
    BoardOperationModel,
    ChatMessageModel,
    apply_board_operations,
    build_board_ai_prompt,
    parse_board_ai_response,
)
from app.board import create_default_board


def test_build_board_ai_prompt_includes_message_history_and_board() -> None:
    board = create_default_board()
    prompt = build_board_ai_prompt(
        board,
        "Move the QA card to done.",
        [ChatMessageModel(role="user", content="Please help with cleanup.")],
    )

    assert "Move the QA card to done." in prompt
    assert "Please help with cleanup." in prompt
    assert '"columns"' in prompt
    assert "create_card" in prompt


def test_parse_board_ai_response_accepts_json_code_fences() -> None:
    parsed = parse_board_ai_response(
        """```json
{"assistant_message":"Done.","operations":[{"type":"delete_card","card_id":"card-2"}]}
```"""
    )

    assert parsed.assistant_message == "Done."
    assert parsed.operations[0].type == "delete_card"
    assert parsed.operations[0].card_id == "card-2"


def test_parse_board_ai_response_rejects_invalid_json() -> None:
    with pytest.raises(AIBoardError, match="Invalid AI response"):
        parse_board_ai_response("not json")


def test_apply_board_operations_updates_board() -> None:
    board = create_default_board()
    updated = apply_board_operations(
        board,
        [
            BoardOperationModel(type="rename_column", column_id="todo", title="Next Up"),
            BoardOperationModel(type="update_card", card_id="card-3", title="Map sign-in flow"),
            BoardOperationModel(type="move_card", card_id="card-5", target_column_id="done", target_index=1),
            BoardOperationModel(
                type="create_card",
                column_id="backlog",
                card_id="card-7",
                title="Write release notes",
                details="Prepare a short MVP summary.",
            ),
            BoardOperationModel(type="delete_card", card_id="card-2"),
        ],
    )

    assert board.columns[1].title == "To Do"
    assert updated.columns[1].title == "Next Up"
    assert updated.columns[4].cards[1].id == "card-5"
    assert updated.columns[0].cards[-1].id == "card-7"
    assert all(card.id != "card-2" for column in updated.columns for card in column.cards)


def test_apply_board_operations_rejects_invalid_operations() -> None:
    board = create_default_board()

    with pytest.raises(AIBoardError, match="Invalid AI operation"):
        apply_board_operations(
            board,
            [BoardOperationModel(type="move_card", card_id="missing-card", target_column_id="done")],
        )


def test_apply_board_operations_maintains_board_integrity() -> None:
    board = create_default_board()
    updated = apply_board_operations(
        board,
        [
            BoardOperationModel(
                type="create_card",
                column_id="backlog",
                card_id="card-99",
                title="Integrity check",
                details="Verify no duplicates.",
            ),
        ],
    )

    all_ids = [card.id for column in updated.columns for card in column.cards]
    assert len(all_ids) == len(set(all_ids)), "Duplicate card IDs after operation"
    assert len(updated.columns) == 5, "Column count must remain 5"
    assert any(card.id == "card-99" for card in updated.columns[0].cards)
