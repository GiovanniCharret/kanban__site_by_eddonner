from pydantic import BaseModel


class CardModel(BaseModel):
    id: str
    title: str
    details: str


class ColumnModel(BaseModel):
    id: str
    title: str
    cards: list[CardModel]


class BoardModel(BaseModel):
    columns: list[ColumnModel]


def create_default_board() -> BoardModel:
    return BoardModel(
        columns=[
            ColumnModel(
                id="backlog",
                title="Backlog",
                cards=[
                    CardModel(
                        id="card-1",
                        title="Customer interview notes",
                        details="Summarize top pain points from three onboarding calls.",
                    ),
                    CardModel(
                        id="card-2",
                        title="Draft launch copy",
                        details="Write hero headline and short value proposition for MVP.",
                    ),
                ],
            ),
            ColumnModel(
                id="todo",
                title="To Do",
                cards=[
                    CardModel(
                        id="card-3",
                        title="Map onboarding flow",
                        details="Define every step and required state transitions.",
                    ),
                ],
            ),
            ColumnModel(
                id="in-progress",
                title="In Progress",
                cards=[
                    CardModel(
                        id="card-4",
                        title="Polish board visuals",
                        details="Tune spacing, shadows, and motion for premium feel.",
                    ),
                ],
            ),
            ColumnModel(
                id="review",
                title="Review",
                cards=[
                    CardModel(
                        id="card-5",
                        title="QA drag and drop",
                        details="Validate keyboard and pointer interactions.",
                    ),
                ],
            ),
            ColumnModel(
                id="done",
                title="Done",
                cards=[
                    CardModel(
                        id="card-6",
                        title="Define MVP scope",
                        details="Finalize strict feature limits for first release.",
                    ),
                ],
            ),
        ],
    )
