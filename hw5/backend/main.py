"""FastAPI backend for the Campus Customs dashboard."""

import json
import shutil
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from .audit import AUDIT_FILE
    from .mcp_client import MCPGateway
    from .team import resolve_ticket
except ImportError:  # Supports `uvicorn main:app` from inside backend/.
    from audit import AUDIT_FILE
    from mcp_client import MCPGateway
    from team import resolve_ticket


ROOT = Path(__file__).resolve().parent.parent
ORIGINAL_DATABASE = ROOT / "data" / "campus_customs.db"
WORKING_DATABASE = ROOT / "data" / "campus_customs_new.db"

app = FastAPI(title="Campus Customs Backend", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    objective: str = "Resolve this ticket safely using verified MCP facts."


class PaymentApproval(BaseModel):
    kind: Literal["invoice", "lease"]
    ref_id: int
    approved_by: str = Field(min_length=1)
    human_approved: bool = True


@app.get("/tickets")
async def tickets() -> list[dict[str, Any]]:
    async with MCPGateway() as gateway:
        result = await gateway.call("ticket_get", {"ticket_id": 101})
        rows = [result] if result.get("found") is not False else []
        for ticket_id in (102, 103):
            row = await gateway.call("ticket_get", {"ticket_id": ticket_id})
            if row.get("found") is not False:
                rows.append(row)
    return [{**row, "state": "resolved" if row.get("status") == "closed" else row.get("status", "open")} for row in rows]


@app.post("/tickets/{ticket_id}/run")
async def run_ticket(ticket_id: int, request: RunRequest | None = None) -> dict[str, Any]:
    try:
        output = await resolve_ticket(ticket_id, request.objective if request else "Resolve this ticket")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        # Keep infrastructure/model failures useful to the dashboard instead of
        # reducing them to the browser's generic "Failed to fetch" message.
        raise HTTPException(status_code=503, detail=f"Agent service unavailable: {exc}") from exc
    return {"ticket_id": ticket_id, "status": "agent_run_completed", "result": output}


@app.get("/agent-events")
async def agent_events(limit: int = Query(default=100, ge=1, le=500)) -> list[dict[str, Any]]:
    if not AUDIT_FILE.exists():
        return []
    events = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
    return events[-limit:]


@app.post("/payments/approve")
async def approve_payment(approval: PaymentApproval) -> dict[str, Any]:
    """The human-only route that invokes the guarded cash-changing MCP tool."""
    if not approval.human_approved:
        raise HTTPException(status_code=400, detail="human approval is required")
    tool = "invoice_pay" if approval.kind == "invoice" else "rent_pay"
    async with MCPGateway() as gateway:
        result = await gateway.call(tool, {"invoice_id" if approval.kind == "invoice" else "lease_id": approval.ref_id, "approved_by": approval.approved_by, "human_approved": True})
    if result.get("ok") is False:
        raise HTTPException(status_code=409, detail=result["error"])
    return result


@app.get("/cash/balance")
async def cash_balance() -> dict[str, Any]:
    async with MCPGateway() as gateway:
        return await gateway.call("cash_check", {"account": "checking"})


@app.post("/reset")
async def reset_database() -> dict[str, str]:
    """Restore the working database while preserving the append-only audit trail."""
    if not ORIGINAL_DATABASE.exists():
        raise HTTPException(status_code=500, detail="original database is missing")
    shutil.copy2(ORIGINAL_DATABASE, WORKING_DATABASE)
    return {"status": "reset", "database": str(WORKING_DATABASE)}
