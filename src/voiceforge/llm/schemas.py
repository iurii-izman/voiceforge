"""Pydantic schemas for Instructor (structured LLM output)."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, field_validator


class ActionItem(BaseModel):
    """One action item from a meeting."""

    description: str = Field(description="What to do")
    assignee: Annotated[str | None, Field(default=None, description="Who is responsible")]
    deadline: Annotated[date | None, Field(default=None, description="Due date")]

    @field_validator("deadline", mode="before")
    @classmethod
    def coerce_unknown_deadline(cls, v: date | str | None) -> Any:
        """Treat '<UNKNOWN>' or empty string as None so LLM output parses."""
        if v is None:
            return None
        if isinstance(v, str) and (not v.strip() or v.strip().upper() == "<UNKNOWN>"):
            return None
        return v


class LiveSummaryOutput(BaseModel):
    """Short live summary: 3–5 key points + action items (for listen --live-summary)."""

    key_points: list[str] = Field(
        default_factory=list,
        description="3–5 key points from the transcript",
    )
    action_items: list[ActionItem] = Field(
        default_factory=list,
        description="Action items if any",
    )


class MeetingAnalysis(BaseModel):
    """Structured analysis of a meeting fragment."""

    questions: list[str] = Field(default_factory=list, description="Questions raised")
    answers: list[str] = Field(default_factory=list, description="Answers or conclusions")
    recommendations: list[str] = Field(default_factory=list, description="Recommendations")
    next_directions: list[str] = Field(default_factory=list, description="Next steps or follow-ups")
    action_items: list[ActionItem] = Field(default_factory=list, description="Action items with assignee and deadline")


class ActionItemStatusUpdate(BaseModel):
    """One action item status update (Block 8.2: LLM says this item is done/cancelled)."""

    id: int = Field(description="Action item id from the list")
    status: Literal["done", "cancelled"] = Field(description="New status: done or cancelled")


class StatusUpdateResponse(BaseModel):
    """LLM response: which open action items are done or cancelled given the transcript."""

    updates: list[ActionItemStatusUpdate] = Field(
        default_factory=list,
        description="List of (id, status) for items mentioned as done or cancelled in the transcript",
    )


# Block 8.3: Meeting template output schemas (each template → own schema)


class StandupOutput(BaseModel):
    """Standup: что сделал, что планирую, блокеры."""

    done: list[str] = Field(default_factory=list, description="What was done since last standup")
    planned: list[str] = Field(default_factory=list, description="What is planned next")
    blockers: list[str] = Field(default_factory=list, description="Blockers or impediments")


class SprintReviewOutput(BaseModel):
    """Sprint review: демо, метрики, фидбэк."""

    demos: list[str] = Field(default_factory=list, description="What was demoed")
    metrics: list[str] = Field(default_factory=list, description="Metrics or KPIs mentioned")
    feedback: list[str] = Field(default_factory=list, description="Feedback from stakeholders")


class OneOnOneOutput(BaseModel):
    """1on1: настроение, рост, блокеры, action items."""

    mood: str = Field(default="", description="How the person is feeling")
    growth: list[str] = Field(default_factory=list, description="Growth or development topics")
    blockers: list[str] = Field(default_factory=list, description="Blockers or concerns")
    action_items: list[ActionItem] = Field(default_factory=list, description="Action items agreed")


class BrainstormOutput(BaseModel):
    """Brainstorm: идеи, голосование, следующие шаги."""

    ideas: list[str] = Field(default_factory=list, description="Ideas proposed")
    voting: list[str] = Field(default_factory=list, description="Votes or preferences expressed")
    next_steps: list[str] = Field(default_factory=list, description="Next steps agreed")


class InterviewOutput(BaseModel):
    """Interview: вопросы кандидату, оценка, решение."""

    questions_asked: list[str] = Field(default_factory=list, description="Questions asked to candidate")
    assessment: list[str] = Field(default_factory=list, description="Assessment or evaluation points")
    decision: str = Field(default="", description="Hire / no hire / follow-up or empty if not decided")
