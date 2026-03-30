"use client";

import { CSS } from "@dnd-kit/utilities";
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useDroppable,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { SortableContext, rectSortingStrategy, sortableKeyboardCoordinates, useSortable } from "@dnd-kit/sortable";
import { ReactNode, useMemo, useState } from "react";
import clsx from "clsx";
import { Column, addCard, deleteCard, moveCard, renameColumn } from "@/lib/kanban";

function GripIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor" aria-hidden="true">
      <circle cx="4.5" cy="3" r="1.3" />
      <circle cx="9.5" cy="3" r="1.3" />
      <circle cx="4.5" cy="7" r="1.3" />
      <circle cx="9.5" cy="7" r="1.3" />
      <circle cx="4.5" cy="11" r="1.3" />
      <circle cx="9.5" cy="11" r="1.3" />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
      <path d="M10 11v6M14 11v6" />
      <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
    </svg>
  );
}

type AddCardFormProps = {
  columnId: string;
  onAddCard: (columnId: string, title: string, details: string) => void;
};

function AddCardForm({ columnId, onAddCard }: AddCardFormProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [details, setDetails] = useState("");

  const reset = () => {
    setTitle("");
    setDetails("");
    setIsOpen(false);
  };

  if (!isOpen) {
    return (
      <button className="add-card-button" onClick={() => setIsOpen(true)} type="button">
        + Add card
      </button>
    );
  }

  return (
    <form
      className="add-card-form"
      onSubmit={(event) => {
        event.preventDefault();
        if (!title.trim()) {
          return;
        }
        onAddCard(columnId, title, details);
        reset();
      }}
    >
      <label className="field-label" htmlFor={`${columnId}-title`}>
        Title
      </label>
      <input
        id={`${columnId}-title`}
        className="field-input"
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        placeholder="Card title"
      />
      <label className="field-label" htmlFor={`${columnId}-details`}>
        Details
      </label>
      <textarea
        id={`${columnId}-details`}
        className="field-textarea"
        value={details}
        onChange={(event) => setDetails(event.target.value)}
        placeholder="Card details"
        rows={3}
      />
      <div className="add-card-actions">
        <button className="primary-button" type="submit">
          Create
        </button>
        <button className="ghost-button" type="button" onClick={reset}>
          Cancel
        </button>
      </div>
    </form>
  );
}

type CardItemProps = {
  cardId: string;
  title: string;
  details: string;
  onDelete: (cardId: string) => void;
};

function CardItem({ cardId, title, details, onDelete }: CardItemProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: cardId });

  return (
    <article
      ref={setNodeRef}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
      }}
      className={clsx("card-item", isDragging && "is-dragging")}
    >
      <div className="card-head">
        <button className="drag-handle" aria-label={`Drag card: ${title}`} type="button" {...attributes} {...listeners}>
          <GripIcon />
        </button>
        <h3 className="card-title">{title}</h3>
        <button className="delete-card-button" type="button" aria-label={`Delete card: ${title}`} onClick={() => onDelete(cardId)}>
          <TrashIcon />
        </button>
      </div>
      {details ? <p className="card-details">{details}</p> : null}
    </article>
  );
}

function CardDragPreview({ title, details }: { title: string; details: string }) {
  return (
    <div className="card-item card-drag-preview">
      <div className="card-head">
        <span className="drag-handle">
          <GripIcon />
        </span>
        <h3 className="card-title">{title}</h3>
      </div>
      {details ? <p className="card-details">{details}</p> : null}
    </div>
  );
}

type ColumnProps = {
  column: Column;
  onRename: (columnId: string, title: string) => void;
  onDeleteCard: (cardId: string) => void;
  onAddCard: (columnId: string, title: string, details: string) => void;
};

function ColumnView({ column, onRename, onDeleteCard, onAddCard }: ColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id: `drop-${column.id}` });

  return (
    <section className="column">
      <header className="column-header">
        <input
          aria-label={`${column.id}-title`}
          className="column-title-input"
          value={column.title}
          onChange={(event) => onRename(column.id, event.target.value)}
        />
        <span className="column-count">{column.cards.length}</span>
      </header>
      <div ref={setNodeRef} className={clsx("column-card-list", isOver && "is-over")} id={`drop-${column.id}`}>
        <SortableContext items={column.cards.map((card) => card.id)} strategy={rectSortingStrategy}>
          {column.cards.map((card) => (
            <CardItem
              key={card.id}
              cardId={card.id}
              title={card.title}
              details={card.details}
              onDelete={onDeleteCard}
            />
          ))}
        </SortableContext>
      </div>
      <AddCardForm columnId={column.id} onAddCard={onAddCard} />
    </section>
  );
}

type KanbanBoardProps = {
  columns: Column[];
  onBoardChange: (columns: Column[]) => void;
  onLogout?: () => void;
  isLoggingOut?: boolean;
  isSaving?: boolean;
  isLoading?: boolean;
  error?: string;
  sidebar?: ReactNode;
};

export function KanbanBoard({
  columns,
  onBoardChange,
  onLogout,
  isLoggingOut = false,
  isSaving = false,
  isLoading = false,
  error = "",
  sidebar,
}: KanbanBoardProps) {
  const [activeCardId, setActiveCardId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  const cardIds = useMemo(() => columns.flatMap((column) => column.cards.map((card) => card.id)), [columns]);

  const activeCard = useMemo(() => {
    if (!activeCardId) return null;
    for (const column of columns) {
      const card = column.cards.find((c) => c.id === activeCardId);
      if (card) return card;
    }
    return null;
  }, [activeCardId, columns]);

  const onDragStart = (event: DragStartEvent) => {
    setActiveCardId(String(event.active.id));
  };

  const onDragEnd = (event: DragEndEvent) => {
    setActiveCardId(null);
    const { active, over } = event;
    if (!over || active.id === over.id) {
      return;
    }
    onBoardChange(moveCard(columns, String(active.id), String(over.id)));
  };

  return (
    <main className="app-shell">
      <header className="hero">
        <div className="hero-top">
          <p className="eyebrow">Single Board MVP</p>
          {onLogout ? (
            <button className="ghost-button hero-action" type="button" onClick={onLogout} disabled={isLoggingOut}>
              {isLoggingOut ? "Logging out..." : "Log out"}
            </button>
          ) : null}
        </div>
        <h1>Kanban Project Board</h1>
        <p className="hero-copy">Move work quickly. Keep scope tight. Ship with confidence.</p>
        {isLoading ? <p className="board-status">Loading board...</p> : null}
        {!isLoading && isSaving ? <p className="board-status">Saving changes...</p> : null}
        {!isLoading && error ? <p className="auth-error board-status">{error}</p> : null}
      </header>

      <div className="workspace-layout">
        <section className="workspace-board" aria-label="Kanban board workspace">
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragStart={onDragStart} onDragEnd={onDragEnd}>
            <div className="kanban-grid">
              <SortableContext items={cardIds} strategy={rectSortingStrategy}>
                {columns.map((column) => (
                  <ColumnView
                    key={column.id}
                    column={column}
                    onRename={(columnId, title) => {
                      const trimmed = title.trim();
                      if (trimmed.length > 0 && trimmed.length <= 100) {
                        onBoardChange(renameColumn(columns, columnId, trimmed));
                      }
                    }}
                    onDeleteCard={(cardId) => onBoardChange(deleteCard(columns, cardId))}
                    onAddCard={(columnId, title, details) => onBoardChange(addCard(columns, columnId, title, details))}
                  />
                ))}
              </SortableContext>
            </div>
            <DragOverlay dropAnimation={{ duration: 180, easing: "ease" }}>
              {activeCard ? <CardDragPreview title={activeCard.title} details={activeCard.details} /> : null}
            </DragOverlay>
          </DndContext>
        </section>
        {sidebar ? <aside className="workspace-sidebar">{sidebar}</aside> : null}
      </div>
    </main>
  );
}
