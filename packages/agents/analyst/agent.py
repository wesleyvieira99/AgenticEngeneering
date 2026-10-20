from packages.tools.registry import list_tickets


def analyze(db, principal):
    tickets = list_tickets(db, principal)
    return {"agent": "analyst", "ticket_count": len(tickets), "open_count": sum(t["status"] == "open" for t in tickets), "tool": "tickets.list"}
