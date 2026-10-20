"""Atlas REST API; every resource lookup includes trusted token tenant identity."""
import asyncio
import json
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import delete, select
from opentelemetry.propagate import inject
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from packages.contracts.models import DocumentInput, Limits, Login, RunInput
from packages.finops.budget import reserve, release_unstarted
from packages.model_gateway.gateway import Gateway
from packages.observability.tracing import configure
from packages.orchestration.engine import Executor, TERMINAL
from packages.orchestration.checkpoints import erase as erase_checkpoint
from packages.retrieval.pipeline import current_documents, document_dict, ingest, reindex
from packages.security.auth import Auth, require_role
from packages.tools.registry import decide_approval, list_tickets
from services.api.db import Approval, Chunk, ContextCache, Database, Document, Event, Memory, Run, Tenant, uid


def run_dict(s, run):
    events = s.scalars(select(Event).where(Event.run_id == run.id, Event.tenant == run.tenant).order_by(Event.id)).all()
    return {"id": run.id, "status": run.status, "question": run.question, "strategy": run.strategy, "answer": run.answer, "sources": run.sources, "events": [{"type": e.type, "data": e.data} for e in events], "usage": run.usage or {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0, "model": "pending"}, "latency_ms": run.latency_ms, "approval_id": run.approval_id, "conversation_id": run.conversation_id, "error": run.error}


def create_app(database_url=None, mode=None):
    db = Database(database_url)
    db.initialize()
    auth = Auth(db)
    gateway = Gateway(mode)
    executor = Executor(db, gateway)
    login_attempts = defaultdict(deque)

    @asynccontextmanager
    async def lifespan(app):
        configure()
        yield
        db.engine.dispose()

    app = FastAPI(title="Atlas", version="0.1.0", lifespan=lifespan)
    app.state.db, app.state.executor, app.state.auth = db, executor, auth
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        FastAPIInstrumentor.instrument_app(app, excluded_urls="api/health")
    origins = os.getenv("ATLAS_CORS_ORIGINS", "http://localhost:5173,http://localhost:4200,http://127.0.0.1:5173,http://127.0.0.1:4200").split(",")
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST", "DELETE", "PUT"], allow_headers=["Authorization", "Content-Type"], expose_headers=[])
    bearer = HTTPBearer(auto_error=False)

    def principal(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if not credentials:
            raise HTTPException(401, "Autenticação necessária")
        return auth.verify(credentials.credentials)

    def owned(s, model, key, tenant):
        obj = s.scalar(select(model).where(model.id == key, model.tenant == tenant))
        if not obj:
            raise HTTPException(404, "Recurso não encontrado")
        return obj

    @app.middleware("http")
    async def body_limit(request, call_next):
        length = request.headers.get("content-length")
        if length and (not length.isdigit() or int(length) > 1_100_000):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Corpo da requisição excede o limite"}, status_code=413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/health")
    def health():
        return {"status": "ok", "mode": gateway.mode}

    @app.post("/api/auth/login")
    def login(data: Login, request: Request):
        key = request.client.host if request.client else "local"
        attempts = login_attempts[key]
        while attempts and attempts[0] < time.monotonic() - 60:
            attempts.popleft()
        if len(attempts) >= 30:
            raise HTTPException(429, "Muitas tentativas; aguarde um minuto")
        attempts.append(time.monotonic())
        identity = auth.login(data.tenant, data.username, data.password)
        return {"access_token": auth.issue(identity), "token_type": "bearer", "tenant": identity.tenant, "role": identity.role}

    @app.get("/api/documents")
    def documents(p=Depends(principal)):
        with db.sessions() as s:
            return [document_dict(d) for d in s.scalars(current_documents(p.tenant).order_by(Document.created_at.desc()))]

    @app.post("/api/documents", status_code=201)
    def upload(data: DocumentInput, p=Depends(principal)):
        require_role(p)
        return ingest(db, p.tenant, data.title, data.content)

    @app.post("/api/documents/reindex")
    def rebuild_embeddings(p=Depends(principal)):
        require_role(p, ("admin",))
        return reindex(db, p.tenant)

    @app.delete("/api/documents/{key}")
    def remove_document(key: str, p=Depends(principal)):
        require_role(p)
        with db.transaction(p.tenant) as s:
            doc = owned(s, Document, key, p.tenant)
            s.execute(delete(Chunk).where(Chunk.document_id == doc.id, Chunk.tenant == p.tenant))
            # Retain metadata as a tombstone so an earlier version cannot revive.
            s.get(Tenant, p.tenant).corpus_version += 1
            s.execute(delete(ContextCache).where(ContextCache.tenant == p.tenant))
        return {"deleted": True}

    @app.post("/api/runs", status_code=202)
    def start(data: RunInput, tasks: BackgroundTasks, p=Depends(principal)):
        if data.question.startswith("/ticket "):
            require_role(p)
        with db.transaction(p.tenant) as s:
            run = Run(id=uid(), tenant=p.tenant, user_id=p.user_id, role=p.role, question=data.question, strategy=data.strategy, conversation_id=data.conversation_id or (uid() if data.memory_enabled else None), memory_enabled=data.memory_enabled, limits={})
            trace_carrier = {}
            inject(trace_carrier)
            run.checkpoint = {"trace": trace_carrier}
            reserve(s, run, gateway)
            s.add(run)
            s.flush()
            db.add_event(s, run, "status", {"status": "queued"})
        if run.strategy != "async":
            tasks.add_task(executor.execute, run.id)
        return {"id": run.id, "status": "queued"}

    @app.get("/api/runs")
    def runs(p=Depends(principal)):
        with db.sessions() as s:
            return [run_dict(s, r) for r in s.scalars(select(Run).where(Run.tenant == p.tenant).order_by(Run.created_at.desc()).limit(50))]

    @app.get("/api/runs/{key}")
    def get_run(key: str, p=Depends(principal)):
        with db.sessions() as s:
            return run_dict(s, owned(s, Run, key, p.tenant))

    @app.get("/api/runs/{key}/events")
    def stream(key: str, p=Depends(principal)):
        with db.sessions() as s:
            owned(s, Run, key, p.tenant)

        async def events():
            cursor = 0
            deadline = time.monotonic() + 310
            while time.monotonic() < deadline:
                with db.sessions() as s:
                    run = owned(s, Run, key, p.tenant)
                    rows = s.scalars(select(Event).where(Event.run_id == key, Event.tenant == p.tenant, Event.id > cursor).order_by(Event.id)).all()
                    for e in rows:
                        cursor = e.id
                        yield f"id: {e.id}\nevent: {e.type}\ndata: {json.dumps(e.data, ensure_ascii=False)}\n\n"
                    if run.status in TERMINAL:
                        yield f"event: done\ndata: {json.dumps(run_dict(s, run), ensure_ascii=False)}\n\n"
                        return
                yield ": heartbeat\n\n"
                await asyncio.sleep(0.15)
        return StreamingResponse(events(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})

    @app.post("/api/runs/{key}/cancel")
    def cancel(key: str, p=Depends(principal)):
        require_role(p)
        with db.transaction(p.tenant) as s:
            run = owned(s, Run, key, p.tenant)
            if run.status in {"queued", "running", "awaiting_approval"}:
                if run.status in {"queued", "awaiting_approval"}:
                    release_unstarted(s, run)
                if run.approval_id:
                    approval = s.get(Approval, run.approval_id)
                    approval.status = "rejected"
                run.status = "cancelled"
                db.add_event(s, run, "status", {"status": "cancelled"})
            return run_dict(s, run)

    @app.post("/api/runs/{key}/resume")
    def resume(key: str, tasks: BackgroundTasks, p=Depends(principal)):
        require_role(p)
        with db.transaction(p.tenant) as s:
            run = owned(s, Run, key, p.tenant)
            if run.status not in {"failed", "cancelled"} or run.reservation_open or run.approval_id:
                raise HTTPException(409, "Retomada exige falha/cancelamento sem reserva ambígua ou ação já preparada")
            if run.usage.get("input_tokens", 0) or run.usage.get("output_tokens", 0):
                raise HTTPException(409, "Tentativa já teve consumo; crie nova execução para preservar atribuição e evitar repetição implícita")
            if run.attempts >= 3:
                raise HTTPException(409, "Dead letter: máximo de três tentativas; crie nova execução após diagnóstico")
            reserve(s, run, gateway)
            run.status, run.error = "queued", None
            db.add_event(s, run, "status", {"status": "queued", "resume": True})
            result = run_dict(s, run)
        if run.strategy != "async":
            tasks.add_task(executor.execute, run.id)
        return result

    @app.get("/api/approvals")
    def approvals(p=Depends(principal)):
        with db.sessions() as s:
            return [{"id": a.id, "run_id": a.run_id, "action": a.action, "arguments": a.arguments, "status": a.status, "expires_at": a.expires_at} for a in s.scalars(select(Approval).where(Approval.tenant == p.tenant))]

    @app.post("/api/approvals/{key}/approve")
    def approve(key: str, p=Depends(principal)):
        return decide_approval(db, p, key, True)

    @app.post("/api/approvals/{key}/reject")
    def reject(key: str, p=Depends(principal)):
        return decide_approval(db, p, key, False)

    @app.get("/api/tickets")
    def tickets(p=Depends(principal)):
        return list_tickets(db, p)

    @app.get("/api/settings")
    def settings(p=Depends(principal)):
        with db.sessions() as s:
            return s.get(Tenant, p.tenant).limits

    @app.put("/api/settings")
    def update_settings(data: Limits, p=Depends(principal)):
        require_role(p, ("admin",))
        if data.max_output_tokens + 256 >= data.max_tokens:
            raise HTTPException(422, "max_tokens deve deixar espaço para entrada")
        with db.transaction(p.tenant) as s:
            s.get(Tenant, p.tenant).limits = data.model_dump()
        return data.model_dump()

    @app.get("/api/usage")
    def usage(p=Depends(principal)):
        with db.sessions() as s:
            tenant = s.get(Tenant, p.tenant)
            records = s.scalars(select(Run).where(Run.tenant == p.tenant)).all()
            successful = sum(r.status == "completed" for r in records)
            return {"input_tokens": sum(r.usage.get("input_tokens", 0) for r in records), "output_tokens": sum(r.usage.get("output_tokens", 0) for r in records), "cost_usd": tenant.used_microdollars / 1_000_000, "runs": len(records), "successful_runs": successful, "cost_per_success_usd": tenant.used_microdollars / 1_000_000 / successful if successful else None, "limits": tenant.limits, "reserved_tokens": tenant.reserved_tokens, "reserved_cost_usd": tenant.reserved_microdollars / 1_000_000, "active_runs": tenant.active_runs}

    @app.delete("/api/conversations/{key}")
    def forget(key: str, p=Depends(principal)):
        with db.transaction(p.tenant) as s:
            s.execute(delete(Memory).where(Memory.tenant == p.tenant, Memory.user_id == p.user_id, Memory.conversation_id == key))
            # Erase user-associated run payloads as well as conversational memory.
            records = s.scalars(select(Run).where(Run.tenant == p.tenant, Run.user_id == p.user_id, Run.conversation_id == key)).all()
            if any(r.status in {"queued", "running"} for r in records):
                raise HTTPException(409, "Cancele execuções ativas antes de apagar a conversa")
            for r in records:
                if r.strategy == "langgraph":
                    erase_checkpoint(db, r)
                r.question, r.answer, r.sources, r.memory_enabled = "[apagado]", "[apagado]", [], False
                s.execute(delete(Event).where(Event.run_id == r.id, Event.tenant == p.tenant))
        return {"deleted": True}

    return app


app = create_app()
