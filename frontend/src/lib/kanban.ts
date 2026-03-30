export type Card = {
  id: string;
  title: string;
  details: string;
};

export type Column = {
  id: string;
  title: string;
  cards: Card[];
};

export const COLUMN_IDS = ["backlog", "todo", "in-progress", "review", "done"] as const;

const DEFAULT_TITLES: Record<(typeof COLUMN_IDS)[number], string> = {
  backlog: "Backlog",
  todo: "To Do",
  "in-progress": "In Progress",
  review: "Review",
  done: "Done",
};

export function createInitialBoard(): Column[] {
  return [
    {
      id: "backlog",
      title: DEFAULT_TITLES.backlog,
      cards: [
        {
          id: "card-1",
          title: "Customer interview notes",
          details: "Summarize top pain points from three onboarding calls.",
        },
        {
          id: "card-2",
          title: "Draft launch copy",
          details: "Write hero headline and short value proposition for MVP.",
        },
      ],
    },
    {
      id: "todo",
      title: DEFAULT_TITLES.todo,
      cards: [
        {
          id: "card-3",
          title: "Map onboarding flow",
          details: "Define every step and required state transitions.",
        },
      ],
    },
    {
      id: "in-progress",
      title: DEFAULT_TITLES["in-progress"],
      cards: [
        {
          id: "card-4",
          title: "Polish board visuals",
          details: "Tune spacing, shadows, and motion for premium feel.",
        },
      ],
    },
    {
      id: "review",
      title: DEFAULT_TITLES.review,
      cards: [
        {
          id: "card-5",
          title: "QA drag and drop",
          details: "Validate keyboard and pointer interactions.",
        },
      ],
    },
    {
      id: "done",
      title: DEFAULT_TITLES.done,
      cards: [
        {
          id: "card-6",
          title: "Define MVP scope",
          details: "Finalize strict feature limits for first release.",
        },
      ],
    },
  ];
}

export function renameColumn(columns: Column[], columnId: string, title: string): Column[] {
  return columns.map((column) => {
    if (column.id !== columnId) {
      return column;
    }

    return {
      ...column,
      title,
    };
  });
}

export function addCard(columns: Column[], columnId: string, title: string, details: string): Column[] {
  const nextId = getNextCardId(columns);
  const cleanTitle = title.trim();
  const cleanDetails = details.trim();

  return columns.map((column) => {
    if (column.id !== columnId) {
      return column;
    }

    return {
      ...column,
      cards: [
        ...column.cards,
        {
          id: nextId,
          title: cleanTitle,
          details: cleanDetails,
        },
      ],
    };
  });
}

export function deleteCard(columns: Column[], cardId: string): Column[] {
  return columns.map((column) => ({
    ...column,
    cards: column.cards.filter((card) => card.id !== cardId),
  }));
}

/**
 * Moves a card within or between columns.
 *
 * @param columns - Current board state.
 * @param activeCardId - ID of the card being dragged.
 * @param overId - Drop target: either a card ID (insert before it) or a drop-zone ID
 *   in the form `"drop-<columnId>"` (append to that column).
 * @returns Updated columns, or the original array unchanged if the move is invalid
 *   (unknown card/column ID, same position, etc.).
 */
export function moveCard(columns: Column[], activeCardId: string, overId: string): Column[] {
  const sourceColumnId = findColumnIdByCardId(columns, activeCardId);
  if (!sourceColumnId) {
    return columns;
  }

  const targetColumnId = overId.startsWith("drop-")
    ? overId.replace("drop-", "")
    : findColumnIdByCardId(columns, overId);

  if (!targetColumnId) {
    return columns;
  }

  const sourceColumnIndex = columns.findIndex((column) => column.id === sourceColumnId);
  const targetColumnIndex = columns.findIndex((column) => column.id === targetColumnId);
  if (sourceColumnIndex === -1 || targetColumnIndex === -1) {
    return columns;
  }

  const sourceColumn = columns[sourceColumnIndex];
  const cardIndex = sourceColumn.cards.findIndex((card) => card.id === activeCardId);
  if (cardIndex === -1) {
    return columns;
  }

  const movingCard = sourceColumn.cards[cardIndex];
  const sourceCards = sourceColumn.cards.filter((card) => card.id !== activeCardId);

  if (sourceColumnId === targetColumnId) {
    if (overId.startsWith("drop-")) {
      return columns;
    }

    const targetIndex = sourceCards.findIndex((card) => card.id === overId);
    if (targetIndex === -1) {
      return columns;
    }

    const reordered = [...sourceCards];
    reordered.splice(targetIndex, 0, movingCard);

    return columns.map((column) =>
      column.id === sourceColumnId
        ? {
            ...column,
            cards: reordered,
          }
        : column,
    );
  }

  const targetColumn = columns[targetColumnIndex];
  const targetCards = [...targetColumn.cards];
  const insertIndex = overId.startsWith("drop-")
    ? targetCards.length
    : Math.max(
        targetCards.findIndex((card) => card.id === overId),
        0,
      );
  targetCards.splice(insertIndex, 0, movingCard);

  return columns.map((column) => {
    if (column.id === sourceColumnId) {
      return { ...column, cards: sourceCards };
    }

    if (column.id === targetColumnId) {
      return { ...column, cards: targetCards };
    }

    return column;
  });
}

export function findColumnIdByCardId(columns: Column[], cardId: string): string | undefined {
  return columns.find((column) => column.cards.some((card) => card.id === cardId))?.id;
}

function getNextCardId(columns: Column[]): string {
  const max = columns
    .flatMap((column) => column.cards)
    .map((card) => Number(card.id.replace("card-", "")))
    .filter((n) => Number.isFinite(n))
    .reduce((acc, n) => Math.max(acc, n), 0);

  return `card-${max + 1}`;
}
