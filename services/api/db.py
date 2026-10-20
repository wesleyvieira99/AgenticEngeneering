"""SQLAlchemy storage. SQLite is the portable teaching mode; PostgreSQL uses pgvector.
Transactions serialize admission and reconciliation per tenant across processes.
"""
import os
import time
from contextlib import contextmanager
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text, create_engine, event, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from packages.contracts.models import Limits


def uid():
    return uuid4().hex


def now():
    return time.time()


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    limits: Mapped[dict] = mapped_column(JSON, default=lambda: Limits().model_dump())
    used_tokens: Mapped[int] = mapped_column(Integer, default=0)
    reserved_tokens: Mapped[int] = mapped_column(Integer, default=0)
    used_microdollars: Mapped[int] = mapped_column(Integer, default=0)
    reserved_microdollars: Mapped[int] = mapped_column(Integer, default=0)
    active_runs: Mapped[int] = mapped_column(Integer, default=0)
    corpus_version: Mapped[int] = mapped_column(Integer, default=0)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    username: Mapped[str] = mapped_column(String)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    title: Mapped[str] = mapped_column(String)
    content_hash: Mapped[str] = mapped_column(String, index=True)
    version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[float] = mapped_column(Float, default=now)


class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant: Mapped[str] = mapped_column(String, index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(Vector(384).with_variant(JSON(), "sqlite"))
    embedding_model: Mapped[str] = mapped_column(String, default="hash-384-v1")


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    question: Mapped[str] = mapped_column(Text)
    strategy: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="queued", index=True)
    answer: Mapped[str] = mapped_column(Text, default="")
    sources: Mapped[list] = mapped_column(JSON, default=list)
    usage: Mapped[dict] = mapped_column(JSON, default=dict)
    limits: Mapped[dict] = mapped_column(JSON)
    latency_ms: Mapped[float] = mapped_column(Float, default=0)
    approval_id: Mapped[str | None] = mapped_column(String, nullable=True)
    conversation_id: Mapped[str | None] = mapped_column(String, nullable=True)
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    reserved_tokens: Mapped[int] = mapped_column(Integer, default=0)
    reserved_microdollars: Mapped[int] = mapped_column(Integer, default=0)
    reservation_open: Mapped[bool] = mapped_column(Boolean, default=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[float] = mapped_column(Float, default=now)
    started_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    checkpoint: Mapped[dict] = mapped_column(JSON, default=dict)


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    tenant: Mapped[str] = mapped_column(String, index=True)
    type: Mapped[str] = mapped_column(String)
    data: Mapped[dict | list] = mapped_column(JSON)
    created_at: Mapped[float] = mapped_column(Float, default=now)


class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant: Mapped[str] = mapped_column(String, index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), unique=True)
    action: Mapped[str] = mapped_column(String)
    arguments: Mapped[dict] = mapped_column(JSON)
    digest: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")
    expires_at: Mapped[float] = mapped_column(Float)


class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant: Mapped[str] = mapped_column(String, index=True)
    approval_id: Mapped[str] = mapped_column(ForeignKey("approvals.id"), unique=True)
    title: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="open")
    created_at: Mapped[float] = mapped_column(Float, default=now)


class Memory(Base):
    __tablename__ = "memories"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    conversation_id: Mapped[str] = mapped_column(String, index=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[float] = mapped_column(Float)


class ContextCache(Base):
    __tablename__ = "context_cache"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    tenant: Mapped[str] = mapped_column(String, index=True)
    corpus_version: Mapped[int] = mapped_column(Integer)
    chunks: Mapped[list] = mapped_column(JSON)
    expires_at: Mapped[float] = mapped_column(Float)


class Database:
    def __init__(self, url=None):
        self.url = url or os.getenv("DATABASE_URL", "sqlite:///./atlas.db")
        args = {"check_same_thread": False, "timeout": 30} if self.url.startswith("sqlite") else {}
        self.engine = create_engine(self.url, connect_args=args, pool_pre_ping=True)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)
        if self.url.startswith("sqlite"):
            @event.listens_for(self.engine, "connect")
            def pragmas(conn, _):
                conn.execute("PRAGMA foreign_keys=ON")
                conn.execute("PRAGMA journal_mode=WAL")

    def initialize(self):
        if self.engine.dialect.name == "postgresql":
            with self.engine.begin() as conn:
                # Serialize migrations across concurrently starting API/worker processes.
                conn.execute(text("SELECT pg_advisory_xact_lock(72641530)"))
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                Base.metadata.create_all(conn)
                conn.execute(text("CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops)"))
        else:
            Base.metadata.create_all(self.engine)

    @contextmanager
    def transaction(self, tenant=None):
        with self.sessions() as session:
            try:
                if self.engine.dialect.name == "sqlite":
                    session.execute(text("BEGIN IMMEDIATE"))
                elif tenant:
                    session.execute(select(Tenant).where(Tenant.id == tenant).with_for_update())
                yield session
                session.commit()
            except BaseException:
                session.rollback()
                raise

    def add_event(self, session, run, kind, data):
        session.add(Event(tenant=run.tenant, run_id=run.id, type=kind, data=data))
