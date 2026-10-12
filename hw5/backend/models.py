from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field


Role = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]


class TicketRequest(BaseModel):
    ticket_id: int
    objective: str = "Resolve the open ticket safely using only verified shop facts."


class AgentStep(BaseModel):
    run_id: str
    agent_id: str
    action: str
    detail: str
    ticket_id: int | None = None
    result: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


@dataclass
class TeamDeps:
    gateway: Any
    run_id: str
    ticket_id: int
    audit: Any
    agents: dict[Role, Any]
    call_stack: list[Role]
    seen_actions: dict[str, int]
