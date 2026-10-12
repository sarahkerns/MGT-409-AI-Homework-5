# Campus Customs — Homework 5

This project is the Campus Customs agent desk. It includes a FastMCP shop-data server, a FastAPI backend, a React/Vite dashboard, the two SQLite databases, testing evidence, and the Problem 10 reflection.

## Dashboard

After starting the backend and frontend, open the Reach Desk here:

**http://localhost:5173**

The dashboard calls the FastAPI backend at `http://localhost:8000`.

## Clean database and environment

The original database is `data/campus_customs.db`. To start a clean working run, copy it over the working database:

```powershell
Copy-Item data/campus_customs.db data/campus_customs_new.db -Force
```

Copy `.env.example` to `.env` and add the Portkey key. Agents use only `gpt-6-luna` through Portkey; never commit the real `.env`.

## Start the MCP server

Install Python dependencies from this folder, then start the server when using an MCP client:

```powershell
pip install -r requirements.txt
python mcp_server/server.py
```

The MCP server reads and updates `data/campus_customs_new.db`.

## Start the FastAPI backend

```powershell
cd backend
uvicorn main:app --reload --port 8000
```

## Start the React board

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` requests to the backend at `http://localhost:8000`.

## Run all three tickets

Before a full three-ticket run, reset the working database either by copying the original database as shown above or by using the backend `POST /reset` route. Record the starting checking balance, then run Tickets 101, 102, and 103 from the board. Payments remain behind the human approval gate.

## Submission layout

The complete submission is contained in the `hw5/` folder, including `AI_prompts.md`, both databases, the MCP server, backend, frontend, and output evidence.
