# Campus Customs MCP server

This FastMCP server provides the only database gateway for agents working on Campus Customs tickets. It uses `data/campus_customs_new.db`, the working copy of the assignment database.

Tools:

- `stock_check(sku, size)` reads `inventory`.
- `rent_info(lease_id)` reads `leases`.
- `price_check(sku)` reads `pricing`.
- `ticket_get(ticket_id)` reads `tickets` before an agent acts.
- `invoice_get(invoice_id)` reads `invoices` and `vendors`.
- `cash_check(account)` reads `cash_accounts`.
- `desk_date()` reads `desk` for the shop date used in overdue checks.
- `ticket_priority(ticket_id)` reads `tickets`, `leases`, and `desk`, and persists a high-priority flag for near-due lease tickets.
- `stock_deduct(ticket_id)` safely updates `inventory` after verifying the ticket and available quantity.
- `invoice_pay(invoice_id, approved_by, human_approved)` updates `payments`, `invoices`, and `cash_accounts` with approval, duplicate-reference, and balance guards.
- `rent_pay(lease_id, approved_by, human_approved)` updates `payments` and `cash_accounts` with the same guards.
- `bulk_price_check(ticket_id, requested_unit_price)` reads `tickets` and `pricing` and rejects prices below unit cost.
- `ticket_close(ticket_id, notes)` updates `tickets` only when a detailed explanation is supplied.

The server is launched through the project MCP connection and is used by the PydanticAI team. It must remain the only shop-data gateway for agents.
