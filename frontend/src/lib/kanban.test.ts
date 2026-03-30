import { describe, expect, it } from "vitest";
import { addCard, createInitialBoard, deleteCard, moveCard, renameColumn } from "./kanban";

describe("kanban state operations", () => {
  it("renames a column", () => {
    const initial = createInitialBoard();
    const updated = renameColumn(initial, "todo", "Planned");
    expect(updated.find((column) => column.id === "todo")?.title).toBe("Planned");
  });

  it("adds a card to a specific column", () => {
    const initial = createInitialBoard();
    const updated = addCard(initial, "done", "Ship MVP", "Deploy and announce");
    const done = updated.find((column) => column.id === "done");
    expect(done?.cards.some((card) => card.title === "Ship MVP")).toBe(true);
  });

  it("deletes a card by id", () => {
    const initial = createInitialBoard();
    const targetId = initial[0].cards[0].id;
    const updated = deleteCard(initial, targetId);
    expect(updated[0].cards.some((card) => card.id === targetId)).toBe(false);
  });

  it("moves a card across columns", () => {
    const initial = createInitialBoard();
    const cardId = initial[0].cards[0].id;
    const targetCardId = initial[1].cards[0].id;

    const updated = moveCard(initial, cardId, targetCardId);
    const todo = updated.find((column) => column.id === "todo");
    const backlog = updated.find((column) => column.id === "backlog");

    expect(todo?.cards.some((card) => card.id === cardId)).toBe(true);
    expect(backlog?.cards.some((card) => card.id === cardId)).toBe(false);
  });

  it("returns original columns when activeCardId is invalid", () => {
    const initial = createInitialBoard();
    const updated = moveCard(initial, "non-existent-card", "drop-todo");
    expect(updated).toEqual(initial);
  });

  it("returns original columns when overId resolves to an unknown column", () => {
    const initial = createInitialBoard();
    const cardId = initial[0].cards[0].id;
    const updated = moveCard(initial, cardId, "drop-unknown-column");
    expect(updated).toEqual(initial);
  });

  it("appends card to column when dropped on column drop zone", () => {
    const initial = createInitialBoard();
    const cardId = initial[0].cards[0].id;
    const updated = moveCard(initial, cardId, "drop-done");
    const done = updated.find((column) => column.id === "done");
    expect(done?.cards[done.cards.length - 1].id).toBe(cardId);
  });
});
