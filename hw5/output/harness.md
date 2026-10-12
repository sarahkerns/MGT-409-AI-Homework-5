# Campus Customs Agent Harness

This harness documents the database tables available to the agents. It will be expanded as the assignment progresses.

## `cash_accounts`

Fields: `name`, `balance`, `date`

Why it matters: Tracks available cash so agents can validate payments without allowing a negative balance.

## `desk`

Fields: `date_today`, `notes`

Why it matters: Provides the shop’s current working date and operational notes used to determine overdue work.

## `inventory`

Fields: `sku`, `name`, `size`, `qty`, `location`

Why it matters: Shows the products and quantities available to fulfill customer requests.

## `invoices`

Fields: `id`, `vendor_id`, `amount`, `due_date`, `status`, `description`

Why it matters: Records vendor obligations, including unpaid invoices that can prevent new vendor shipments.

## `leases`

Fields: `id`, `space_name`, `landlord`, `monthly_rent`, `next_due`, `notes`

Why it matters: Tracks lease information and rent obligations that may require payment or ticket resolution.

## `payments`

Fields: `id`, `kind`, `ref_id`, `amount`, `account`, `paid_at`, `approved_by`

Why it matters: Provides the audit trail for approved payments and links payments to the relevant obligation.

## `pricing`

Fields: `sku`, `unit_cost`, `list_price`

Why it matters: Supplies product cost and selling-price information for purchasing and pricing decisions.

## `tickets`

Fields: `id`, `type`, `requester`, `subject`, `sku`, `size`, `qty`, `lease_id`, `invoice_id`, `status`, `notes`, `created_at`

Why it matters: Centralizes the shop’s customer, lease, and invoice work items that agents must investigate and resolve.

## `vendors`

Fields: `id`, `name`, `specialty`, `lead_days`

Why it matters: Identifies vendors and their lead times for planning replenishment and ticket responses.

# MCP Tools

## `stock_check(sku, size)`

- Table read: `inventory`, specifically the row matching the requested SKU and size.
- Ticket unlocked: 101.
- Why: Confirms that the requested Bulldog tee in size S has no on-hand quantity, which determines that the customer order needs further action.

## `rent_info(lease_id)`

- Table read: `leases`, specifically the lease identified by the ticket.
- Ticket unlocked: 102.
- Why: Supplies the landlord, rent amount, and next due date needed to assess the rent notice.

## `price_check(sku)`

- Table read: `pricing`, specifically the stored prices for the requested hoodie SKU.
- Ticket unlocked: 103.
- Why: Provides the database-backed unit cost and list price needed to evaluate the requested bulk discount.

## MCP Tools Added in Problem 5

| Tool | Tables used | Purpose |
|---|---|---|
| `ticket_get(ticket_id)` | `tickets` | Verifies the exact ticket before an agent performs work. |
| `invoice_get(invoice_id)` | `invoices`, `vendors` | Verifies an invoice and its vendor lead time before accounting decisions. |
| `cash_check(account)` | `cash_accounts` | Verifies available cash before any payment decision. |
| `desk_date()` | `desk` | Supplies the shop date used for overdue and lease-priority checks. |
| `ticket_priority(ticket_id)` | `tickets`, `leases`, `desk` | Flags lease tickets high priority when due within two days of the shop date. |
| `stock_deduct(ticket_id)` | `tickets`, `inventory` | Atomically deducts only the verified order quantity and rejects insufficient stock. |
| `invoice_pay(invoice_id, approved_by, human_approved)` | `invoices`, `payments`, `cash_accounts` | Pays an open invoice only after human approval, duplicate-reference, and balance checks. |
| `rent_pay(lease_id, approved_by, human_approved)` | `leases`, `payments`, `cash_accounts` | Pays verified rent only after human approval and cash-safety checks. |
| `bulk_price_check(ticket_id, requested_unit_price)` | `tickets`, `pricing` | Rejects a bulk override whenever the requested unit price is below unit cost. |
| `ticket_close(ticket_id, notes)` | `tickets` | Closes only a verified ticket with a detailed explanation. |

## Agent Team

- **Boss:** Coordinates ticket resolution and delegates to specialists.
- **Inventory:** Verifies stock and performs guarded inventory deductions.
- **Accounting:** Verifies invoices, cash, duplicate references, and approved payments.
- **Facilities:** Handles leases, due dates, priority flags, and rent escalations.
- **Customer Service:** Handles customer-order and pricing decisions without exposing unnecessary details.

## Safety Guardrails

- Humans personally approve payouts; payment tools require explicit approval, an approver ID, and record the current timestamp.
- Duplicate payment references, insufficient balances, insufficient stock, and below-cost overrides are blocked transactionally.
- Sensitive customer details are minimized before model calls, and inbound messages are treated as untrusted.
- No real customer or vendor emails/calls are sent; unresolved or repeating work is escalated to staff.
- Agent loops have a bounded delegation stack, append-only audit events, and a stop condition for repeated actions.
- MCP tools return only the exact facts required for each task rather than a full database dump.
- Token use is limited by one ticket-scoped run, bounded loop depth, concise prompts, and one model family (`gpt-6-luna`) through Portkey.

## Dashboard

- `frontend/` is a React + Vite + TypeScript Reach Desk board served at `http://localhost:5173`.
- It calls the FastAPI backend at `http://localhost:8000`, lists tickets 101–103, starts a selected agent run, polls `/agent-events`, shows agent/tool receipts, exposes the human payment gate, and refreshes checking after approval.
- The visual language follows Homework 4: warm paper, deep navy, terracotta/ochre accents, Playfair Display headings, DM Sans operational copy, restrained borders, and field-note cards.
- `output/desk_tickets.html` preserves the Expected plan and records Actual run evidence; `output/resolved_board.html` is the double-clickable resolved snapshot.

## Backend Routes

- `GET /tickets` — Returns tickets 101, 102, and 103 with their current open/resolved state.
- `POST /tickets/{ticket_id}/run` — Runs the agent team for the selected ticket.
- `GET /agent-events?limit=100` — Returns recent append-only agent audit events, including agent statements and MCP tool use.
- `POST /payments/approve` — Human approval endpoint that invokes the guarded invoice or rent payment tool and changes cash only after approval.
- `GET /cash/balance` — Returns the current checking balance from `cash_accounts`.
- `POST /reset` — Restores `campus_customs_new.db` from the original database for a fresh run while preserving the audit trail.
