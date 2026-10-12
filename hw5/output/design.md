# Problem 8: Agent dashboard design

## Direction

The dashboard is a warm, paper-like Reach Desk for the Campus Customs team. It follows the Homework 4 visual language: a warm paper background (`#F8F5EE`), deep navy (`#0A1C2A`) for structure, terracotta (`#D97757`) and ochre (`#8C3B2B`) for actions and attention, and subtle warm borders (`#E5DFD3`). Playfair Display is used for editorial headings and DM Sans for compact operational copy.

The layout keeps the ticket rail on the left and the selected ticket’s working board on the right. A checking-balance card is always visible near the top so cash is treated as a first-class operational fact. The design uses restrained borders, small rounded-free field-note cards, and gentle hover movement rather than heavy shadows.

## Agent communication

Each agent has a compact card with a colored initial, role label, loop state, latest message, and the MCP tool currently being used. Boss is navy, Inventory is green, Accounting is ochre, Facilities is gold, and Customer Service is terracotta. Tool calls are shown as short receipts so the board distinguishes evidence gathering from agent handoffs.

The agents use a breezy, playful Southern California conversational flavor—light “like” language and candid handoffs inspired by the requested SNL sketch—while keeping the actual business facts precise and never inventing shop data.

## State and human gates

Tickets are selected from the left rail and show Open or Resolved status. A completed run marks the selected ticket resolved in the board and refreshes the recent audit events for the Actual-style summary. Payment controls are separated into a Human gate card: agents can prepare a payment, but only the human approval button calls the cash-changing backend route. The checking card refreshes immediately after approval so a balance drop is visible.
