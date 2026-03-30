"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { Column } from "@/lib/kanban";

type SessionResponse = {
  authenticated: boolean;
  username?: string;
};

type ApiError = {
  detail?: string;
};

type BoardResponse = {
  columns: Column[];
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type BoardOperation = {
  type: "create_card" | "update_card" | "move_card" | "delete_card" | "rename_column";
  column_id?: string | null;
  card_id?: string | null;
  title?: string | null;
  details?: string | null;
  target_column_id?: string | null;
  target_index?: number | null;
};

type AIChatResponse = {
  assistant_message: string;
  operations: BoardOperation[];
  board: BoardResponse;
};

const API = {
  SESSION: "/api/session",
  LOGIN: "/api/login",
  LOGOUT: "/api/logout",
  BOARD: "/api/board",
  AI_CHAT: "/api/ai/chat",
} as const;

const CHAT_RENDER_LIMIT = 50;   // max messages shown in the thread
const CHAT_HISTORY_LIMIT = 10;  // max messages sent to the AI

async function readJson<T>(response: Response): Promise<T> {
  return (await response.json()) as T;
}

function formatOperation(operation: BoardOperation): string {
  switch (operation.type) {
    case "create_card":
      return `Created ${operation.title ?? operation.card_id ?? "a card"}`;
    case "update_card":
      return `Updated ${operation.card_id ?? "a card"}`;
    case "move_card":
      return `Moved ${operation.card_id ?? "a card"} to ${operation.target_column_id ?? "another column"}`;
    case "delete_card":
      return `Deleted ${operation.card_id ?? "a card"}`;
    case "rename_column":
      return `Renamed ${operation.column_id ?? "a column"} to ${operation.title ?? "a new title"}`;
    default:
      return operation.type;
  }
}

export function AppShell() {
  const [authState, setAuthState] = useState<"loading" | "guest" | "authenticated">("loading");
  const [boardState, setBoardState] = useState<"idle" | "loading" | "ready">("idle");
  const [columns, setColumns] = useState<Column[]>([]);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSavingBoard, setIsSavingBoard] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatError, setChatError] = useState("");
  const [isChatSubmitting, setIsChatSubmitting] = useState(false);
  const [lastOperations, setLastOperations] = useState<BoardOperation[]>([]);
  const boardRequestId = useRef(0);

  useEffect(() => {
    let isActive = true;

    const loadSession = async () => {
      try {
        const response = await fetch(API.SESSION);
        const session = await readJson<SessionResponse>(response);
        if (!isActive) {
          return;
        }

        setAuthState(session.authenticated ? "authenticated" : "guest");
      } catch {
        if (!isActive) {
          return;
        }

        setAuthState("guest");
        setError("Unable to reach the server.");
      }
    };

    void loadSession();

    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    if (authState !== "authenticated") {
      setBoardState("idle");
      setColumns([]);
      setChatMessages([]);
      setChatInput("");
      setChatError("");
      setLastOperations([]);
      return;
    }

    let isActive = true;

    const loadBoard = async () => {
      setBoardState("loading");
      setError("");

      try {
        const response = await fetch(API.BOARD);
        if (!response.ok) {
          const payload = await readJson<ApiError>(response);
          throw new Error(payload.detail ?? "Unable to load the board.");
        }

        const board = await readJson<BoardResponse>(response);
        if (!isActive) {
          return;
        }

        setColumns(board.columns);
        setChatMessages([
          {
            role: "assistant",
            content: "Board synced. Ask me to create, update, move, delete cards, or rename a column.",
          },
        ]);
        setLastOperations([]);
        setBoardState("ready");
      } catch (loadError) {
        if (!isActive) {
          return;
        }

        setBoardState("idle");
        setError(loadError instanceof Error ? loadError.message : "Unable to load the board.");
      }
    };

    void loadBoard();

    return () => {
      isActive = false;
    };
  }, [authState]);

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const response = await fetch(API.LOGIN, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const payload = await readJson<ApiError>(response);
        setError(payload.detail ?? "Unable to sign in.");
        return;
      }

      setPassword("");
      setAuthState("authenticated");
    } catch {
      setError("Unable to sign in right now.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = async () => {
    setIsSubmitting(true);
    setError("");

    try {
      await fetch(API.LOGOUT, { method: "POST" });
    } finally {
      setAuthState("guest");
      setBoardState("idle");
      setColumns([]);
      setPassword("");
      setChatMessages([]);
      setChatInput("");
      setChatError("");
      setLastOperations([]);
      setIsSubmitting(false);
    }
  };

  const handleBoardChange = async (nextColumns: Column[]) => {
    if (boardState !== "ready") {
      return;
    }

    const previousColumns = columns;
    const requestId = boardRequestId.current + 1;
    boardRequestId.current = requestId;

    setColumns(nextColumns);
    setIsSavingBoard(true);
    setError("");

    try {
      const response = await fetch(API.BOARD, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ columns: nextColumns }),
      });

      if (!response.ok) {
        const payload = await readJson<ApiError>(response);
        throw new Error(payload.detail ?? "Unable to save board changes.");
      }

      const savedBoard = await readJson<BoardResponse>(response);
      if (boardRequestId.current === requestId) {
        setColumns(savedBoard.columns);
      }
    } catch (saveError) {
      if (boardRequestId.current === requestId) {
        setColumns(previousColumns);
        setError(saveError instanceof Error ? saveError.message : "Unable to save board changes.");
      }
    } finally {
      if (boardRequestId.current === requestId) {
        setIsSavingBoard(false);
      }
    }
  };

  const handleChatSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const message = chatInput.trim();

    if (!message || boardState !== "ready" || isChatSubmitting) {
      return;
    }

    const nextMessages = [...chatMessages, { role: "user" as const, content: message }];
    setChatMessages(nextMessages);
    setChatInput("");
    setChatError("");
    setIsChatSubmitting(true);

    try {
      const response = await fetch(API.AI_CHAT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          history: chatMessages.slice(-CHAT_HISTORY_LIMIT),
        }),
      });

      if (!response.ok) {
        const payload = await readJson<ApiError>(response);
        throw new Error(payload.detail ?? "Unable to send the AI request.");
      }

      const payload = await readJson<AIChatResponse>(response);
      setChatMessages([
        ...nextMessages,
        {
          role: "assistant",
          content: payload.assistant_message,
        },
      ]);
      setLastOperations(payload.operations);
      setColumns(payload.board.columns);
      setError("");
    } catch (chatRequestError) {
      setChatMessages(chatMessages);
      setChatError(chatRequestError instanceof Error ? chatRequestError.message : "Unable to send the AI request.");
    } finally {
      setIsChatSubmitting(false);
    }
  };

  const sidebar = (
    <section className="chat-panel">
      <div className="chat-panel-head">
        <p className="eyebrow">AI Sidebar</p>
        <h2>Board Copilot</h2>
        <p className="chat-copy">Ask for board changes in plain language and I will update the board when the backend confirms them.</p>
      </div>

      <div className="chat-thread" aria-label="AI conversation">
        {chatMessages.slice(-CHAT_RENDER_LIMIT).map((message, index) => (
          <article
            key={`${message.role}-${index}-${message.content}`}
            className={`chat-bubble ${message.role === "assistant" ? "is-assistant" : "is-user"}`}
          >
            <p className="chat-role">{message.role === "assistant" ? "AI" : "You"}</p>
            <p className="chat-text">{message.content}</p>
          </article>
        ))}
      </div>

      <div className="chat-ops">
        <p className="chat-ops-title">Latest applied changes</p>
        {lastOperations.length ? (
          <ul className="chat-ops-list">
            {lastOperations.map((operation, index) => (
              <li key={`${operation.type}-${index}`}>{formatOperation(operation)}</li>
            ))}
          </ul>
        ) : (
          <p className="chat-ops-empty">No AI board changes yet.</p>
        )}
      </div>

      <form className="chat-form" onSubmit={handleChatSubmit}>
        <label className="field-label" htmlFor="chat-message">
          Message
        </label>
        <textarea
          id="chat-message"
          className="field-textarea chat-input"
          rows={4}
          placeholder="Try: Move QA drag and drop to Done and rename To Do to Next Up."
          value={chatInput}
          onChange={(event) => setChatInput(event.target.value)}
          disabled={boardState !== "ready" || isChatSubmitting}
        />
        {chatError ? <p className="auth-error">{chatError}</p> : null}
        <button className="primary-button chat-submit" type="submit" disabled={boardState !== "ready" || isChatSubmitting}>
          {isChatSubmitting ? "Sending..." : "Send to AI"}
        </button>
      </form>
    </section>
  );

  if (authState === "loading") {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <p className="eyebrow">Phase 4</p>
          <h1>Loading board access</h1>
          <p className="auth-copy">Checking your local session.</p>
        </section>
      </main>
    );
  }

  if (authState === "authenticated") {
    return (
      <KanbanBoard
        columns={columns}
        onBoardChange={handleBoardChange}
        onLogout={handleLogout}
        isLoggingOut={isSubmitting}
        isSaving={isSavingBoard}
        isLoading={boardState !== "ready"}
        error={error}
        sidebar={sidebar}
      />
    );
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="eyebrow">Local MVP Sign-In</p>
        <h1>Sign in to your board</h1>
        <p className="auth-copy">Use the hardcoded credentials for the local MVP: user / password.</p>
        <form className="auth-form" onSubmit={handleLogin}>
          <label className="field-label" htmlFor="username">
            Username
          </label>
          <input
            id="username"
            className="field-input"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
          <label className="field-label" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            className="field-input"
            autoComplete="current-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {error ? <p className="auth-error">{error}</p> : null}
          <button className="primary-button auth-submit" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}
