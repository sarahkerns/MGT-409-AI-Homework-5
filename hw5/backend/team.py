import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

from pydantic_ai import Agent, RunContext

try:
    from .audit import append_audit
    from .config import luna_model
    from .models import Role, TeamDeps
except ImportError:  # Supports loading through `uvicorn main:app` from backend/.
    from audit import append_audit
    from config import luna_model
    from models import Role, TeamDeps


PROMPTS = Path(__file__).resolve().parent / "prompts"
ROLES: tuple[Role, ...] = ("boss", "inventory", "accounting", "facilities", "customer_service")
TOOL_GUIDE = """
Exact MCP tool names (do not invent aliases): ticket_get, invoice_get, cash_check,
stock_check, rent_info, price_check, desk_date, ticket_priority, stock_deduct, invoice_pay,
rent_pay, bulk_price_check, ticket_close. Call these through mcp_tool only.
Tool results are internal evidence. In your final update, translate them into short plain-English sentences. Never echo tool names, function arguments, JSON, markdown evidence lists, or raw database fields.
"""


def _prompt(role: Role) -> str:
    return (PROMPTS / f"{role}.md").read_text(encoding="utf-8")


def _make_agent(role: Role, model: Any) -> Agent:
    agent = Agent(model, system_prompt=f"{_prompt(role)}\n\n{TOOL_GUIDE}", model_settings={"openai_reasoning_effort": "none"})

    @agent.tool
    async def mcp_tool(ctx: RunContext[TeamDeps], tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a named MCP tool; all shop facts must come from this gateway."""
        action_key = f"{role}:{tool_name}:{json.dumps(arguments, sort_keys=True)}"
        ctx.deps.seen_actions[action_key] = ctx.deps.seen_actions.get(action_key, 0) + 1
        if ctx.deps.seen_actions[action_key] > 2:
            append_audit({"run_id": ctx.deps.run_id, "agent_id": role, "action": "safety_stop", "ticket_id": ctx.deps.ticket_id, "tool": tool_name, "reason": "repeated identical action; staff notification required"})
            return {"ok": False, "error": "safety stop: repeated action blocked; notify staff"}
        result = await ctx.deps.gateway.call(tool_name, arguments)
        append_audit({"run_id": ctx.deps.run_id, "agent_id": role, "action": "mcp_tool", "ticket_id": ctx.deps.ticket_id, "tool": tool_name, "arguments": arguments, "result": result})
        return result

    @agent.tool
    async def delegate(ctx: RunContext[TeamDeps], target: Role, task: str) -> str:
        """Delegate to another connected role with a bounded loop."""
        if target in ctx.deps.call_stack or len(ctx.deps.call_stack) >= 5:
            return "Delegation blocked by loop safety limit. Escalate to a human."
        peer = ctx.deps.agents[target]
        ctx.deps.call_stack.append(target)
        try:
            result = await run_agent(peer, target, task, ctx.deps)
            return result.output
        finally:
            ctx.deps.call_stack.pop()
    return agent


def build_team(gateway: Any) -> dict[Role, Agent]:
    model = luna_model()
    return {role: _make_agent(role, model) for role in ROLES}


async def run_agent(agent: Agent, role: Role, task: str, deps: TeamDeps):
    append_audit({"run_id": deps.run_id, "agent_id": role, "action": "loop_start", "ticket_id": deps.ticket_id, "task": task})
    result = await agent.run(task, deps=deps)
    append_audit({"run_id": deps.run_id, "agent_id": role, "action": "loop_end", "ticket_id": deps.ticket_id, "said": str(result.output)})
    return result


async def resolve_ticket(ticket_id: int, objective: str = "Resolve this ticket") -> str:
    run_id = str(uuid.uuid4())
    try:
        from .mcp_client import MCPGateway
    except ImportError:
        from mcp_client import MCPGateway
    async with MCPGateway() as gateway:
        ticket = await gateway.call("ticket_get", {"ticket_id": ticket_id})
        if not ticket or ticket.get("found") is False:
            raise ValueError(f"Ticket {ticket_id} was not found")
        append_audit({"run_id": run_id, "agent_id": "system", "action": "ticket_verified", "ticket_id": ticket_id, "result": ticket})
        agents = build_team(gateway)
        deps = TeamDeps(gateway=gateway, run_id=run_id, ticket_id=ticket_id, audit=append_audit, agents=agents, call_stack=["boss"], seen_actions={})
        result = await run_agent(agents["boss"], "boss", f"{objective}. Verified ticket: {json.dumps(ticket)}", deps)
        return result.output


if __name__ == "__main__":
    asyncio.run(resolve_ticket(101))
