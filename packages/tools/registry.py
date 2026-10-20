"""Policy enforcement point: trusted principal + exact action; documents grant no rights."""
import hashlib
import hmac
import json
from fastapi import HTTPException
from sqlalchemy import select

from packages.contracts.models import TicketArguments
from packages.security.auth import require_role
from services.api.db import Approval, Run, Ticket, now, uid


def action_digest(tenant, run_id, action, arguments):
    canonical = json.dumps({"tenant": tenant, "run_id": run_id, "action": action, "arguments": arguments}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def ticket_dict(ticket):
    return {"id": ticket.id, "title": ticket.title, "status": ticket.status, "created_at": ticket.created_at}


def list_tickets(db, principal):
    with db.sessions() as s:
        return [ticket_dict(t) for t in s.scalars(select(Ticket).where(Ticket.tenant == principal.tenant).order_by(Ticket.created_at.desc()).limit(20))]


def propose_ticket(db, principal, run_id, title):
    require_role(principal)
    args = TicketArguments(title=title).model_dump()
    with db.transaction(principal.tenant) as s:
        run = s.scalar(select(Run).where(Run.id == run_id, Run.tenant == principal.tenant))
        if not run or run.user_id != principal.user_id:
            raise HTTPException(404, "Execução não encontrada")
        existing = s.scalar(select(Approval).where(Approval.run_id == run_id))
        if existing:
            return existing.id
        approval = Approval(id=uid(), tenant=principal.tenant, run_id=run_id, action="ticket.create", arguments=args, digest=action_digest(principal.tenant, run_id, "ticket.create", args), expires_at=now() + 900)
        s.add(approval)
        run.approval_id = approval.id
        return approval.id


def decide_approval(db, principal, approval_id, approve):
    require_role(principal, ("admin",))
    with db.transaction(principal.tenant) as s:
        approval = s.scalar(select(Approval).where(Approval.id == approval_id, Approval.tenant == principal.tenant))
        if not approval:
            raise HTTPException(404, "Aprovação não encontrada")
        existing = s.scalar(select(Ticket).where(Ticket.approval_id == approval.id, Ticket.tenant == principal.tenant))
        if approval.status == "approved" and approve:
            return {"status": "approved", "ticket_id": existing.id}
        if approval.status != "pending":
            raise HTTPException(409, "Aprovação já decidida")
        if approval.expires_at < now():
            raise HTTPException(409, "Aprovação expirada; solicite nova operação")
        expected = action_digest(approval.tenant, approval.run_id, approval.action, approval.arguments)
        if not hmac.compare_digest(expected, approval.digest) or approval.action != "ticket.create":
            raise HTTPException(409, "Ação divergente da aprovação")
        run = s.get(Run, approval.run_id)
        if run.status != "awaiting_approval":
            raise HTTPException(409, "Execução não está aguardando aprovação")
        approval.status = "approved" if approve else "rejected"
        run.status = "completed" if approve else "cancelled"
        result = {"status": approval.status}
        if approve:
            args = TicketArguments.model_validate(approval.arguments)
            ticket = Ticket(id=uid(), tenant=principal.tenant, approval_id=approval.id, title=args.title)
            s.add(ticket)
            result["ticket_id"] = ticket.id
            run.answer += f"\nTicket criado: {ticket.id}"
        db.add_event(s, run, "tool", {"action": "ticket.create", "decision": approval.status, "approval_id": approval.id, "actor": principal.user_id, "digest": approval.digest})
        db.add_event(s, run, "status", {"status": run.status})
        return result
