"""Campus Customs MCP tools.

All shop facts and database mutations are exposed here so agents do not
create a second, bypassing data-access layer.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

DATABASE = Path(__file__).resolve().parent.parent / "data" / "campus_customs_new.db"
mcp = FastMCP("campus-customs")


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def _row(connection: sqlite3.Connection, query: str, parameters: tuple[Any, ...]) -> dict[str, Any] | None:
    result = connection.execute(query, parameters).fetchone()
    return dict(result) if result else None


def _error(message: str) -> dict[str, Any]:
    return {"ok": False, "error": message}


@mcp.tool()
def stock_check(sku: str, size: str) -> dict[str, Any]:
    """Look up the current quantity and location for a product size."""
    with _connect() as connection:
        row = _row(connection, "SELECT sku, name, size, qty, location FROM inventory WHERE sku = ? AND size = ?", (sku, size))
    return row or {"sku": sku, "size": size, "found": False}


@mcp.tool()
def rent_info(lease_id: int) -> dict[str, Any]:
    """Look up the rent obligation for a lease."""
    with _connect() as connection:
        row = _row(connection, "SELECT id, space_name, landlord, monthly_rent, next_due, notes FROM leases WHERE id = ?", (lease_id,))
    return row or {"lease_id": lease_id, "found": False}


@mcp.tool()
def price_check(sku: str) -> dict[str, Any]:
    """Look up the stored unit cost and list price for a product."""
    with _connect() as connection:
        row = _row(connection, "SELECT sku, unit_cost, list_price FROM pricing WHERE sku = ?", (sku,))
    return row or {"sku": sku, "found": False}


@mcp.tool()
def ticket_get(ticket_id: int) -> dict[str, Any]:
    """Fetch one ticket before any agent acts on it."""
    with _connect() as connection:
        row = _row(connection, "SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    return row or {"ticket_id": ticket_id, "found": False}


@mcp.tool()
def invoice_get(invoice_id: int) -> dict[str, Any]:
    """Fetch one invoice and its vendor lead time."""
    with _connect() as connection:
        row = _row(connection, """SELECT i.*, v.name AS vendor_name, v.lead_days
            FROM invoices i LEFT JOIN vendors v ON v.id = i.vendor_id WHERE i.id = ?""", (invoice_id,))
    return row or {"invoice_id": invoice_id, "found": False}


@mcp.tool()
def cash_check(account: str = "checking") -> dict[str, Any]:
    """Read the current cash balance."""
    with _connect() as connection:
        row = _row(connection, "SELECT name, balance, date FROM cash_accounts WHERE name = ?", (account,))
    return row or {"account": account, "found": False}


@mcp.tool()
def desk_date() -> dict[str, Any]:
    """Read the shop's working date used for overdue and priority checks."""
    with _connect() as connection:
        row = _row(connection, "SELECT date_today, notes FROM desk LIMIT 1", ())
    return row or {"found": False}


@mcp.tool()
def ticket_priority(ticket_id: int) -> dict[str, Any]:
    """Flag a lease ticket high priority when its due date is within two days of shop date."""
    with _connect() as connection:
        ticket = _row(connection, "SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        if not ticket:
            return _error(f"ticket {ticket_id} was not found")
        if not ticket["lease_id"]:
            return {"ok": True, "ticket_id": ticket_id, "priority": "normal", "reason": "ticket has no lease"}
        desk = _row(connection, "SELECT date_today FROM desk LIMIT 1", ())
        lease = _row(connection, "SELECT id, next_due FROM leases WHERE id = ?", (ticket["lease_id"],))
        if not desk or not lease:
            return _error("desk date or lease was not found")
        days = (datetime.fromisoformat(lease["next_due"]) - datetime.fromisoformat(desk["date_today"])).days
        priority = "high" if days <= 2 else "normal"
        if priority == "high" and not (ticket["notes"] or "").startswith("[HIGH PRIORITY]"):
            notes = f"[HIGH PRIORITY] {ticket['notes'] or ''}".strip()
            connection.execute("UPDATE tickets SET notes = ? WHERE id = ?", (notes, ticket_id))
        return {"ok": True, "ticket_id": ticket_id, "priority": priority, "days_until_due": days, "date_today": desk["date_today"], "next_due": lease["next_due"]}


@mcp.tool()
def stock_deduct(ticket_id: int) -> dict[str, Any]:
    """Deduct the exact SKU, size, and quantity from a verified customer ticket."""
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        ticket = _row(connection, "SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        if not ticket:
            return _error(f"ticket {ticket_id} was not found")
        if ticket["type"] != "customer_order" or not ticket["sku"] or not ticket["size"] or not ticket["qty"]:
            return _error("ticket is not a complete customer order")
        item = _row(connection, "SELECT * FROM inventory WHERE sku = ? AND size = ?", (ticket["sku"], ticket["size"]))
        if not item:
            return _error("inventory item was not found")
        if item["qty"] < ticket["qty"]:
            return _error(f"insufficient stock: have {item['qty']}, need {ticket['qty']}")
        new_qty = item["qty"] - ticket["qty"]
        connection.execute("UPDATE inventory SET qty = ? WHERE sku = ? AND size = ?", (new_qty, ticket["sku"], ticket["size"]))
        return {"ok": True, "ticket_id": ticket_id, "sku": ticket["sku"], "size": ticket["size"], "deducted": ticket["qty"], "remaining": new_qty}


def _pay(kind: str, reference_id: int, amount: float, approved_by: str, human_approved: bool, description: str) -> dict[str, Any]:
    if not human_approved or not approved_by.strip():
        return _error("human approval and approved_by are required")
    if amount <= 0:
        return _error("payment amount must be positive")
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        if _row(connection, "SELECT id FROM payments WHERE kind = ? AND ref_id = ?", (kind, reference_id)):
            return _error("duplicate payment reference is blocked")
        account = _row(connection, "SELECT name, balance FROM cash_accounts WHERE name = 'checking'", ())
        if not account or account["balance"] < amount:
            return _error("payment refused: insufficient cash")
        now = datetime.now(timezone.utc).isoformat()
        connection.execute("UPDATE cash_accounts SET balance = balance - ? WHERE name = 'checking'", (amount,))
        connection.execute("INSERT INTO payments(kind, ref_id, amount, account, paid_at, approved_by) VALUES (?, ?, ?, 'checking', ?, ?)", (kind, reference_id, amount, now, approved_by))
        if kind == "invoice":
            connection.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (reference_id,))
        return {"ok": True, "kind": kind, "ref_id": reference_id, "amount": amount, "account": "checking", "paid_at": now, "approved_by": approved_by, "description": description}


@mcp.tool()
def invoice_pay(invoice_id: int, approved_by: str, human_approved: bool = False) -> dict[str, Any]:
    """Pay a verified open invoice after explicit human approval."""
    with _connect() as connection:
        invoice = _row(connection, "SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    if not invoice:
        return _error(f"invoice {invoice_id} was not found")
    if invoice["status"] != "open":
        return _error("invoice is not open")
    return _pay("invoice", invoice_id, invoice["amount"], approved_by, human_approved, invoice["description"] or "")


@mcp.tool()
def rent_pay(lease_id: int, approved_by: str, human_approved: bool = False) -> dict[str, Any]:
    """Pay a verified lease obligation after explicit human approval."""
    with _connect() as connection:
        lease = _row(connection, "SELECT * FROM leases WHERE id = ?", (lease_id,))
    if not lease:
        return _error(f"lease {lease_id} was not found")
    return _pay("lease", lease_id, lease["monthly_rent"], approved_by, human_approved, f"{lease['space_name']} rent")


@mcp.tool()
def bulk_price_check(ticket_id: int, requested_unit_price: float) -> dict[str, Any]:
    """Evaluate a verified bulk-price request without allowing a price below unit cost."""
    with _connect() as connection:
        ticket = _row(connection, "SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        if not ticket:
            return _error(f"ticket {ticket_id} was not found")
        pricing = _row(connection, "SELECT * FROM pricing WHERE sku = ?", (ticket["sku"],))
    if not pricing:
        return _error("pricing record was not found")
    if requested_unit_price < pricing["unit_cost"]:
        return _error(f"price override rejected: {requested_unit_price} is below unit cost {pricing['unit_cost']}")
    return {"ok": True, "ticket_id": ticket_id, "sku": ticket["sku"], "requested_unit_price": requested_unit_price, "unit_cost": pricing["unit_cost"], "list_price": pricing["list_price"]}


@mcp.tool()
def ticket_close(ticket_id: int, notes: str) -> dict[str, Any]:
    """Close a verified ticket only with a detailed explanation."""
    if len(notes.strip()) < 20:
        return _error("closed tickets require a detailed explanation in notes")
    with _connect() as connection:
        ticket = _row(connection, "SELECT id FROM tickets WHERE id = ?", (ticket_id,))
        if not ticket:
            return _error(f"ticket {ticket_id} was not found")
        connection.execute("UPDATE tickets SET status = 'closed', notes = ? WHERE id = ?", (notes.strip(), ticket_id))
    return {"ok": True, "ticket_id": ticket_id, "status": "closed", "notes": notes.strip()}


if __name__ == "__main__":
    mcp.run()
