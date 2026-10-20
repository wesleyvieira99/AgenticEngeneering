"""Opt-in per-user episodic memory with seven-day retention and explicit deletion."""
from sqlalchemy import delete, select
from services.api.db import Memory, now


def recall(db, run):
    if not run.memory_enabled or not run.conversation_id:
        return []
    with db.sessions() as s:
        rows = s.scalars(select(Memory).where(Memory.tenant == run.tenant, Memory.user_id == run.user_id, Memory.conversation_id == run.conversation_id, Memory.expires_at > now()).order_by(Memory.expires_at.desc()).limit(4)).all()
        return [{"question": r.question, "answer": r.answer} for r in reversed(rows)]


def remember(session, run):
    session.execute(delete(Memory).where(Memory.expires_at < now()))
    if run.memory_enabled and run.conversation_id:
        session.add(Memory(tenant=run.tenant, user_id=run.user_id, conversation_id=run.conversation_id, question=run.question, answer=run.answer, expires_at=now() + 7 * 86400))
