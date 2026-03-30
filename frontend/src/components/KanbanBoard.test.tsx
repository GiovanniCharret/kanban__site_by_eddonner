import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { KanbanBoard } from "./KanbanBoard";
import { createInitialBoard } from "@/lib/kanban";

describe("KanbanBoard", () => {
  it("renders five columns", () => {
    render(<KanbanBoard columns={createInitialBoard()} onBoardChange={() => {}} />);
    expect(screen.getByLabelText("backlog-title")).toBeInTheDocument();
    expect(screen.getByLabelText("todo-title")).toBeInTheDocument();
    expect(screen.getByLabelText("in-progress-title")).toBeInTheDocument();
    expect(screen.getByLabelText("review-title")).toBeInTheDocument();
    expect(screen.getByLabelText("done-title")).toBeInTheDocument();
  });

  it("adds and deletes a card", () => {
    let columns = createInitialBoard();
    const handleBoardChange = (nextColumns: typeof columns) => {
      columns = nextColumns;
      rerender(<KanbanBoard columns={columns} onBoardChange={handleBoardChange} />);
    };
    const { rerender } = render(<KanbanBoard columns={columns} onBoardChange={handleBoardChange} />);

    fireEvent.click(screen.getAllByRole("button", { name: "+ Add card" })[0]);
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "New task" } });
    fireEvent.change(screen.getByLabelText("Details"), { target: { value: "Keep it minimal" } });
    fireEvent.click(screen.getByRole("button", { name: "Create" }));

    expect(screen.getByText("New task")).toBeInTheDocument();

    const deleteButton = screen.getByRole("button", { name: "Delete card: New task" });

    expect(deleteButton).toBeDefined();
    fireEvent.click(deleteButton);

    expect(screen.queryByText("New task")).not.toBeInTheDocument();
  });
});
