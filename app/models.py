"""Pydantic models shared across the app."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

IssueType = Literal["bug", "regression", "feature_request", "how_to", "billing", "performance"]


class Customer(BaseModel):
    id: str
    name: str
    company: str
    plan: Literal["Starter", "Growth", "Enterprise"]
    region: str
    environment: str  # e.g. "Snowflake warehouse, 12 seats"
    csm: str


class Ticket(BaseModel):
    id: str
    customer_id: str
    created_at: datetime
    product: str
    version: str
    module: str
    issue_type: IssueType
    subject: str
    body: str
    status: Literal["open", "resolved"] = "open"
    resolution: str | None = None


class TicketWithCustomer(BaseModel):
    ticket: Ticket
    customer: Customer


class Citation(BaseModel):
    """A single memory the agent grounded its answer in."""

    kind: Literal["customer_history", "known_issue", "emerging_issue", "kb"]
    text: str
    score: float | None = None
    tags: list[str] = Field(default_factory=list)
    source_fact_ids: list[str] = Field(default_factory=list)


class ToolCallTrace(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result_preview: str = ""
    error: str | None = None


class DraftResult(BaseModel):
    ticket_id: str
    mode: Literal["memory", "amnesia"]
    draft: str
    citations: list[Citation] = Field(default_factory=list)
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    used_memory: bool = False
    elapsed_ms: int = 0
    error: str | None = None


class KnownIssue(BaseModel):
    id: str
    name: str
    content: str
    last_refreshed_at: datetime | None = None
    is_stale: bool | None = None
