from packages.tools.registry import propose_ticket


def prepare(db, principal, run_id, title):
    return propose_ticket(db, principal, run_id, title)
