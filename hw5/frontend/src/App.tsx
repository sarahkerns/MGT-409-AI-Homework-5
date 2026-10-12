import { useEffect, useMemo, useState } from 'react'

// Vite proxies this same-origin path to the local FastAPI server.
const API = '/api'
const AGENTS = ['boss', 'inventory', 'accounting', 'facilities', 'customer_service'] as const
type Agent = typeof AGENTS[number]

type Ticket = {
  id: number; type: string; subject: string; requester: string; status: string; state: string
  sku?: string | null; size?: string | null; qty?: number | null; notes?: string | null
  lease_id?: number | null; invoice_id?: number | null
}
type Event = { run_id?: string; agent_id: string; action: string; ticket_id?: number; said?: string; tool?: string; result?: unknown; task?: string }
type Cash = { name: string; balance: number; date: string }

const agentLabels: Record<Agent, string> = {
  boss: 'Boss', inventory: 'Inventory', accounting: 'Accounting', facilities: 'Facilities', customer_service: 'Customer Service'
}

async function getJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, { headers: { 'Content-Type': 'application/json' }, ...options })
  if (!response.ok) {
    const body = await response.text()
    let detail = body
    try { detail = (JSON.parse(body) as { detail?: string }).detail ?? body } catch { /* plain-text response */ }
    throw new Error(detail || `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

function agentLine(agent: Agent, event?: Event) {
  if (!event) return agent === 'boss' ? 'Like, ready to coordinate the desk.' : 'Standing by for the boss.'
  if (event.action === 'mcp_tool') return `Like, checking ${event.tool} with the desk records.`
  if (event.action === 'safety_stop') return 'Whoa, repeating that move is blocked — staff should take it from here.'
  if (event.action === 'loop_end') return event.said || 'Done with the handoff.'
  return event.task || 'Working the ticket with the team.'
}

function App() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [selectedId, setSelectedId] = useState(101)
  const [events, setEvents] = useState<Event[]>([])
  const [cash, setCash] = useState<Cash | null>(null)
  const [running, setRunning] = useState(false)
  const [resolved, setResolved] = useState<number[]>([])
  const [message, setMessage] = useState('Desk is ready.')
  const [showApproval, setShowApproval] = useState(false)

  const selected = tickets.find((ticket) => ticket.id === selectedId)
  const selectedEvents = events.filter((event) => event.ticket_id === selectedId)
  const latestByAgent = useMemo(() => {
    const latest = new Map<string, Event>()
    selectedEvents.forEach((event) => latest.set(event.agent_id, event))
    return latest
  }, [selectedEvents])

  async function refresh() {
    const [nextTickets, nextCash, nextEvents] = await Promise.all([
      getJson<Ticket[]>('/tickets'), getJson<Cash>('/cash/balance'), getJson<Event[]>('/agent-events?limit=100')
    ])
    setTickets(nextTickets); setCash(nextCash); setEvents(nextEvents)
  }

  useEffect(() => { refresh().catch((error: Error) => setMessage(`Desk connection issue: ${error.message}`)) }, [])
  useEffect(() => {
    if (tickets.length > 0) return
    const timer = window.setInterval(() => {
      refresh().catch(() => undefined)
    }, 1500)
    return () => window.clearInterval(timer)
  }, [tickets.length])
  useEffect(() => {
    if (!running) return
    const timer = window.setInterval(() => { getJson<Event[]>('/agent-events?limit=100').then(setEvents).catch(() => undefined) }, 1200)
    return () => window.clearInterval(timer)
  }, [running])

  async function runSelected() {
    setRunning(true); setMessage(`Calling the Boss on ticket ${selectedId}...`)
    try {
      await getJson(`/tickets/${selectedId}/run`, { method: 'POST', body: JSON.stringify({ objective: 'Resolve this ticket and report each safe action clearly.' }) })
      setResolved((current) => current.includes(selectedId) ? current : [...current, selectedId])
      setMessage(`Ticket ${selectedId} run finished. Actual results are ready for review.`)
      await refresh()
    } catch (error) { setMessage(`Run stopped: ${(error as Error).message}`) }
    finally { setRunning(false) }
  }

  async function approveRent() {
    try {
      await getJson('/payments/approve', { method: 'POST', body: JSON.stringify({ kind: 'lease', ref_id: selected?.lease_id ?? 1, approved_by: 'Human operator', human_approved: true }) })
      setShowApproval(false); setMessage('Rent payment approved and checking balance refreshed.'); await refresh()
    } catch (error) { setMessage(`Payment was not made: ${(error as Error).message}`) }
  }

  return <div className="app-shell">
    <header className="topbar">
      <div className="brand-wrap"><div className="brand-badge">R</div><div><div className="brand-title">Reach Desk</div><div className="brand-subtitle">Campus Customs · New Haven field office</div></div></div>
      <div className="date-note">Agent operations / <strong>{cash?.date ?? '—'}</strong></div>
    </header>
    <main className="page-content">
      <section className="hero-panel"><div><div className="eyebrow">Desk field note</div><h1>Keep the tickets moving,<br /><em>with receipts.</em></h1><p className="lede">A warm, candid view of what the team knows, what it is doing, and where a human needs to step in.</p></div><div className="cash-card"><span>Checking balance</span><strong>${cash?.balance.toFixed(2) ?? '—'}</strong><small>Updates after human approval</small></div></section>
      <div className="status-line"><span className="status-dot" />{message}</div>
      <section className="workspace">
        <aside className="ticket-rail"><div className="section-kicker">Open desk</div><h2>Tickets</h2>{tickets.map((ticket) => <button className={`ticket-card ${ticket.id === selectedId ? 'selected' : ''}`} key={ticket.id} onClick={() => setSelectedId(ticket.id)}><span className="ticket-number">#{ticket.id}</span><strong>{ticket.subject}</strong><span>{ticket.requester}</span><b className={resolved.includes(ticket.id) || ticket.state === 'resolved' ? 'resolved' : ''}>{resolved.includes(ticket.id) || ticket.state === 'resolved' ? 'Resolved' : 'Open'}</b></button>)}</aside>
        <section className="desk-board"><div className="board-heading"><div><div className="section-kicker">Selected ticket · #{selected?.id}</div><h2>{selected?.subject ?? 'Loading desk'}</h2><p>{selected?.notes ?? 'Select a ticket to inspect its plan.'}</p></div><button className="primary-btn" disabled={running || !selected} onClick={runSelected}>{running ? 'Team is running…' : 'Start agent team'}</button></div>
          <div className="agent-grid">{AGENTS.map((agent) => <article className={`agent-card agent-${agent}`} key={agent}><div className="agent-head"><span className="agent-icon">{agentLabels[agent][0]}</span><div><strong>{agentLabels[agent]}</strong><small>{latestByAgent.get(agent)?.action === 'mcp_tool' ? 'Reading the board' : 'Agent loop'}</small></div></div><p>{agentLine(agent, latestByAgent.get(agent))}</p>{latestByAgent.get(agent)?.tool && <code>{latestByAgent.get(agent)?.tool}</code>}</article>)}</div>
          <div className="lower-grid"><section className="summary-card"><div className="section-kicker">Run notes</div><h3>What the team did</h3>{selectedEvents.length ? <ul>{selectedEvents.slice(-6).map((event, index) => <li key={`${event.agent_id}-${event.action}-${index}`}><strong>{agentLabels[event.agent_id as Agent] ?? event.agent_id}</strong> {event.action === 'mcp_tool' ? `used ${event.tool}` : event.action === 'loop_end' ? 'reported back' : event.action.replace('_', ' ')}</li>)}</ul> : <p className="muted">Run the team to see the specialist handoffs and tool receipts here.</p>}</section><section className="approval-card"><div className="section-kicker">Human gate</div><h3>Payment or purchase approval</h3><p>Agents can prepare a pay. Only a human click changes cash.</p>{selected?.id === 102 && <>{showApproval ? <div className="approval-actions"><button className="primary-btn" onClick={approveRent}>Approve rent payment</button><button className="text-btn" onClick={() => setShowApproval(false)}>Cancel</button></div> : <button className="secondary-btn" onClick={() => setShowApproval(true)}>Review rent approval</button>}</>}</section></div>
        </section>
      </section>
    </main>
  </div>
}

export default App
