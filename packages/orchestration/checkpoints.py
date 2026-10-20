"""LangGraph durable savers; keys include tenant, user and run, never client input.
Checkpoint payloads may contain evidence/history; deletion must include this store.
"""
from contextlib import contextmanager
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from sqlalchemy import text


def thread_id(run):
    return f"{run.tenant}:{run.user_id}:{run.id}"


@contextmanager
def saver(db):
    if db.engine.dialect.name == "postgresql":
        connection = db.url.replace("postgresql+psycopg://", "postgresql://", 1)
        with PostgresSaver.from_conn_string(connection) as checkpoint:
            with db.engine.begin() as migration:
                migration.execute(text("SELECT pg_advisory_xact_lock(72641532)"))
                checkpoint.setup()
            yield checkpoint
    else:
        path = str(db.engine.url.database) + ".checkpoints.db"
        with SqliteSaver.from_conn_string(path) as checkpoint:
            checkpoint.setup()
            yield checkpoint


def erase(db, run):
    with saver(db) as checkpoint:
        checkpoint.delete_thread(thread_id(run))
