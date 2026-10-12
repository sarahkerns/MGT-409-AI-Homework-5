# AI Prompts

## Problem 10: Reflection

### Prompt

Problem 10: Reflection

Open output/desk_tickets.html and fill the Reflection tab. Run spell check before writing it. Evaluate the agents on Tickets 101, 102, and 103; compare Actual with Expected; explain when a single agent would be simpler; identify new problems the team could and could not solve; and tie every answer to the app, the three ticket runs, and the Ticket and Cash tabs as evidence.

## Problem 1: Vibe coder prompts

### Prompt

We will be working in the Homework 5 folder today.

Problem 1: Vibe coder prompts

Create AI_prompts.md and keep it updated as we work together today. This file will be a log of what I type to you.

There should be one section for each problem. Each section must include:

1. The problem number and title
2. The prompt I type to you
3. If I need a follow up prompt (more than one prompt per problem), ask me to give you one sentence on what was lacking after the first prompt to store in this file as well

### Follow-up prompt

This is just an FYI for you as we work together today. Here are the rules of the data provided in the Homework 5 folder:

1. The field desk.date_today is "totay" for the shop. Use this date to determine what is overdue.
2. Vendor lead times come from the vendors table.
3. A vendor will not ship new product while they still have an open unpaid invoice
4. Human approval is required for any payments. If payment is made, make sure to update the relevant table.
5. If there is not enough cash, the pay tool must refuse so that there are never any negative balances.
6. Cash only goes out in this task today - we did not model revenue, so no money comes in.
7. Before a full run to resolve the tiskets, make sure to reset the database to the original values.
8. Do NOT email customers or call real vendors - drafts should not leave the board

Use my port key that is the in the .env file in the root folder. Use only GPT-6-Luna through Portkey for every agent. There should be NO OTHER MODELS in my code or runs.

### What was lacking after the first prompt

I decided to add the rules for the baseline of the assignment in problem 1, before beginning the work.

## Problem 2: Study the Campus Customs database

### Prompt

Problem 2: Study the Campus Customs database.

Copy the original data/campus_customs.db file and copy it to data/campus_customs_new.db. Late problems will update this working copy.

Start output/harness.md. For each table, list the fields and one short line on why that table matters for the agents.

This harness file will keep growing in later problems.

## Problem 3: Build the MCP server

### Prompt

Problem 3: Build the MCP server

Write an MCP server in mcp_server/ using FastMCP. It will talk to data/campus_customs_new.db. Do NOT connect it or run it in this problem.

Every agent in this homework uses the tools in this MCP server. Later on, we will add more rools to it, but for now, write three tools you know you will need for the tickets in the database. Keep the names short and clear. Never invent any data, only use information in the database.

In output/harness.md, list each of the three MCP tools. For every tool include:

1. Which table it reads
2. Which ticket it helsps unlock (101, 102, or 103)
3. One short sentence on why that tool is the write one for that ticket

Don't use vaue lines like "reads inventory" - be clear, specific, but concise - tie the tool to the ticket.

Also add a short mcp_server/README.md file that explains what the MCP server is for, which database file it uses, and the three tools it has.

## Problem 4: Add the MCP server to vibe coder and test each tool

### Prompt

Problem 4: Add the MCP server to vibe coder and test each tool

Add the MCP server to this project so that you can call the tools. Save the connection JSON text in .mcp.json in the Homework 4 folder.

With Codex connected, walk me through testing each of the three MCP tools. Save the evidence in output/mcp_smoke.json. For every tool include, we will need:

1. The prompt I asked the vibe coder
2. The tool name
3. The tool output (must match values in data/campus_customs_new.db)

## Problem 5: Build the agent team and grow the MCP tools

### Prompt

Problem 5: Build the agent team and grow the MCP tools

Build the agentic team for Campus Customs using PydanticAI: Boss, Inventory, Accounting, Facilities, and Customer Service. Include protms, models, and agent loops so they can delegate work to each other with full connectivity.

Put the agent prompts in backend/prompts with ONE FILE PER AGENT. Put data types in backend/models.py, and the agent files under backend/ (the layout can vary as long as the five roles are clear). Use my PORTKEY_API_KEY and only use gpt-6-luna for every agent.

Below are the rules the agent will need so they can work on the open tickets. Shop facts come from the MCP server over data/campus_customs_new.db - do not invent a second shop-tools later that bypasses MCP.

1. Agents must fetch and verify the specific ticket_id, invoice_id, or lease_id before invoking any mutation tool.
2. Reject inventory deductions with an error if available stock is insufficient, and block block duplicate payments by checking existing reference IDs and available cash balance before decrementing accounts.
3. Automatically reject any bulk or price override where the requested unit price drops below pricing.unit_cost.
4. Flag tickets as high-priority and require cash-balance verification whenever leases.next_due is within 2 days of desk.date_today.
5. Every payment must log the agent ID in approved_by and current timestamp in paid_at, and no ticket may transition to closed without a detailed explanation in notes.

Wire the agents so they append to output/audit_trail.json as they run: for each agent-loop step, record enough to audit later. Append to this file - do not wipe it each run.

In output/harness.md, list each agent and each MCP tool, included the ones added in this problem, along with which table the tool uses. Also add a short safety section: the garudarails a real bueinss would want when agents touch real customs and real money, plus limits that keep token use in check. Here is the safety guidelines:

A human must personally approve large payouts, and the system must block accidental double charges if a transaction gets retried. The software should hide sensitive customer details from the AI and filter incoming messages so shoppers cannot trick the bot into giving unauthorized discounts. Strict safety limits must automatically shut down the assistant and notify staff if it gets stuck repeating the same action over and over. Finally, the system should only feed the AI the exact facts it needs for each order instead of full database files, keeping the tool running quickly and preventing expensive computational waste.

Update mcp_server/README.md so the tool list matches what you have now.

## Problem 6: Plan the three tickets

### Prompt

Problem 6: Plan the three tickets

Build output/desk_tickets.hml - a page you can double-click with one tab per ticket (101, 102, and 103). Also add empty Cash and Reflection tabs for later problems (add a "To be completed later" note for now).

One each tab, fill an Expected section only (leave room for an Actual section you will will fill after you run the agents).

For each ticket's Expected section, write the following:

101:

- Who the boss should call first, and why: The Inventory Agent, because what needs to happen first is checking whether a size small Classic Bulldog Tee is in stock at the aisle location.
- Agent delegations: Inventory agent
- MCP tools used: read_inventory, update_ticket_status

102:

- Who the boss should call first, and why: The Finance Agent because this is a rent payment due in 48 hours, which will require verifying that the amount of money is covered in the bank abbount for the rent disbursement.
- Agent delegations: Finance Agent
- MCP tools used: read_leases, read_cash_accounts) execute_payment, update_ticket_status

103:

- Who the boss should call first, and why: The Sales Agent becuase the shop needs to confirm the discount can be used.
- Agent delegations:  Pricing and Inventory Agents
- MCP tools used: read_pricing, read_inventory, update_ticket_status

## Problem 7: Backend routes

### Prompt

Problem 7: Backend routes

The React frontend dashboard (next problem) needs a backend it can call. In backend/main.py, use FastAPI and add routes that can do the following:

1. Return the three tickets and whether each is open or resolved
2. Take a ticket ID and run the agent team on that ticket
3. Return recent agent events - what each agent said and which tools they used - so the board can refresh
4. Approve a payment or purchase after a human clicks approve (agents only prepare the pay; this route is what actually changes cash)
5. Return the current checking balance from cash_accounts
6. Reset the database to the original values when you want to try a fresh run

From the backend/ folder, start the server with:

uvicorn main:app --reload --port 8000

This turns on the backend at http://localhost:8000 so the front end can call those routes.

In output/harness.md, list each route in one list (what URL / what it does).

## Problem 8: Agent dashboard

### Prompt

Problem 8: Agent dashboard

Build the front end dashboard in frontend/ with React + Vite + TypeScript. The page should call the routes built in Problem 7. The board should list all three tickets, let the user pick one and start the agent team, show each agent’s current message or action, mark a ticket resolved when the run finishes, show a summary of each agent’s work, let a human approve a pay or purchase when asked, and show the checking balance after an approved payment.

Make the style and vibe consistent with Homework 4. Use the backend at http://localhost:8000, allow the Vite origin, start with npm run dev, and document the layout, agent differentiation, resolved tickets, cash display, and Californians-inspired voice in output/design.md.

## Problem 9: Resolve the tickets

### Prompt

Problem 9: Resolve the tickets:

Before testing the agents on a full run over the three tickets, reset the working database data/campus_customs_new.db again so we can start clean. Note the starting checking balance, then run all three tickets on the board (101, 102, 103) until each is resolved.

Open output/desk_tickets.html from Problem 6. On each ticket tab, fill the Actual section from this run: which agents worked, what they delegated, and which tools they used. Keep the Expected section so I can compare the two.

On the cash tab of the same output/desk_tickets.html, itemize the starting balance, each ticket’s cash change and reason, and the ending balance matching cash_accounts.

Also save output/resolved_tickets.json, output/resolved_board.html, append real runs to output/audit_trail.json, and finish output/harness.md with tables, MCP tools, agents, API routes, dashboard, and safety rules.

### Follow-up prompt

Going back to Problem 9 updates - can you fix the agents so that their summaries are in conversational english to give updates on what they are working on? For example, this is what Accounting says right now: Invoice **501** matches ticket **101**: it’s for a rush reprint of **CC-TEE-WHITE, size S**. The invoice status is **open**, for **$840**, with a due date of **August 28, 2026**. Ticket 101 is also **open** and references invoice 501. The cash check showed **$3,400** in checking as of August 31, 2026. No payment was made or approved

This should be in plain english, speaking like a character from teh SNL skit, the Californitans

### Additional follow-up prompt

On ticket #103, the Accounting agent has the underlying MCP tool wording. Can you fix so it is in plain English? Here is what it says: Ticket 103 is an open bulk hoodie discount request for 20 size-M hoodies, SKU CC-HOOD-NAVY. The ticket does not specify a requested unit price. Exact MCP evidence: - - `ticket_get(ticket_id="103")` → ticket 103, requester Yale AI Club, SKU `CC-HOOD-NAVY`, size `M`, quantity `20`, status `open`. - `bulk_price_check(ticket_id=103, sku="CC-HOOD-NAVY", size="M", qty=20, requested_unit_price=0)` → rejected: “0.0 is below unit cost 22.0.” - `bulk_price_check(ticket_id=103, sku="CC-HOOD-NAVY", size="M", qty=20, requested_unit_price=22)` → `ok: true`; unit cost `$22.00`, list price `$58.00`. Defensible decision: the lowest supported unit price is **$22.00**, which equals cost; any price below that is below cost. The check does not establish that a bulk discount is otherwise authorized, so confirm the customer’s requested price and obtain the required approval before offering a discount. No payment was approved.

