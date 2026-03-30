import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AppShell } from "./AppShell";

const fetchMock = vi.fn();

describe("AppShell", () => {
  afterEach(() => {
    fetchMock.mockReset();
    vi.unstubAllGlobals();
  });

  it("shows the sign-in form when the session is not authenticated", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ authenticated: false }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<AppShell />);

    expect(await screen.findByRole("heading", { name: "Sign in to your board" })).toBeInTheDocument();
  });

  it("signs in and logs out through the API", async () => {
    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ authenticated: false }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ authenticated: true, username: "user" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            columns: [
              { id: "backlog", title: "Backlog", cards: [] },
              { id: "todo", title: "To Do", cards: [] },
              { id: "in-progress", title: "In Progress", cards: [] },
              { id: "review", title: "Review", cards: [] },
              { id: "done", title: "Done", cards: [] },
            ],
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ authenticated: false }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<AppShell />);

    await screen.findByRole("heading", { name: "Sign in to your board" });

    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "user" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "password" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Kanban Project Board" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Log out" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Sign in to your board" })).toBeInTheDocument();
    });

    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/session");
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username: "user", password: "password" }),
    });
    expect(fetchMock).toHaveBeenNthCalledWith(3, "/api/board");
    expect(fetchMock).toHaveBeenNthCalledWith(4, "/api/logout", { method: "POST" });
  });

  it("persists board changes through the API after loading the board", async () => {
    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ authenticated: true, username: "user" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            columns: [
              { id: "backlog", title: "Backlog", cards: [] },
              { id: "todo", title: "To Do", cards: [] },
              { id: "in-progress", title: "In Progress", cards: [] },
              { id: "review", title: "Review", cards: [] },
              { id: "done", title: "Done", cards: [] },
            ],
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            columns: [
              { id: "backlog", title: "Ideas", cards: [] },
              { id: "todo", title: "To Do", cards: [] },
              { id: "in-progress", title: "In Progress", cards: [] },
              { id: "review", title: "Review", cards: [] },
              { id: "done", title: "Done", cards: [] },
            ],
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<AppShell />);

    await screen.findByLabelText("backlog-title");

    fireEvent.change(screen.getByLabelText("backlog-title"), { target: { value: "Ideas" } });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenNthCalledWith(3, "/api/board", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          columns: [
            { id: "backlog", title: "Ideas", cards: [] },
            { id: "todo", title: "To Do", cards: [] },
            { id: "in-progress", title: "In Progress", cards: [] },
            { id: "review", title: "Review", cards: [] },
            { id: "done", title: "Done", cards: [] },
          ],
        }),
      });
    });
  });

  it("sends chat requests and refreshes the board from the AI response", async () => {
    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ authenticated: true, username: "user" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            columns: [
              { id: "backlog", title: "Backlog", cards: [] },
              { id: "todo", title: "To Do", cards: [] },
              { id: "in-progress", title: "In Progress", cards: [] },
              { id: "review", title: "Review", cards: [] },
              { id: "done", title: "Done", cards: [] },
            ],
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            assistant_message: "I renamed the column and added the card.",
            operations: [
              { type: "rename_column", column_id: "todo", title: "Next Up" },
              { type: "create_card", column_id: "todo", card_id: "card-7", title: "Plan release notes", details: "Draft the MVP release summary." },
            ],
            board: {
              columns: [
                { id: "backlog", title: "Backlog", cards: [] },
                {
                  id: "todo",
                  title: "Next Up",
                  cards: [{ id: "card-7", title: "Plan release notes", details: "Draft the MVP release summary." }],
                },
                { id: "in-progress", title: "In Progress", cards: [] },
                { id: "review", title: "Review", cards: [] },
                { id: "done", title: "Done", cards: [] },
              ],
            },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<AppShell />);

    await screen.findByLabelText("todo-title");

    fireEvent.change(screen.getByLabelText("Message"), {
      target: { value: "Rename To Do to Next Up and add a release notes card there." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send to AI" }));

    expect(await screen.findByText("I renamed the column and added the card.")).toBeInTheDocument();
    expect(screen.getByLabelText("todo-title")).toHaveValue("Next Up");
    expect(screen.getByText("Plan release notes")).toBeInTheDocument();
    expect(screen.getByText("Renamed todo to Next Up")).toBeInTheDocument();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenNthCalledWith(3, "/api/ai/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: "Rename To Do to Next Up and add a release notes card there.",
          history: [
            {
              role: "assistant",
              content: "Board synced. Ask me to create, update, move, delete cards, or rename a column.",
            },
          ],
        }),
      });
    });
  });
});
