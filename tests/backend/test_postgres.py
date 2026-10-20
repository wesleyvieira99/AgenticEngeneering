"""Real pgvector test, opt in with ATLAS_TEST_DATABASE_URL. Uses isolated schema."""
import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from services.api.main import create_app
from services.api.db import Database
from .conftest import auth, run


@pytest.mark.integration
def test_postgres_vector_and_budget_transaction(monkeypatch):
    url = os.getenv("ATLAS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("ATLAS_TEST_DATABASE_URL not configured")
    monkeypatch.setenv("ATLAS_EMBEDDING_MODE", "hash")
    schema = "atlas_test_" + uuid4().hex
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    parsed = make_url(url).update_query_dict({"options": f"-csearch_path={schema},public"})
    initializers = [Database(parsed.render_as_string(hide_password=False)) for _ in range(3)]
    # Explicit schema translation keeps PostgreSQL's public tables out of the
    # inspector's checkfirst lookup; startup remains concurrent and initially empty.
    for database in initializers:
        database.engine = database.engine.execution_options(schema_translate_map={None: schema})
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda database: database.initialize(), initializers))
    for database in initializers:
        database.engine.dispose()
    app = create_app(parsed.render_as_string(hide_password=False), "deterministic")
    try:
        with TestClient(app) as client:
            headers = auth(client)
            response = client.post("/api/documents", headers=headers, json={"title": "Política", "content": "Reembolso em sete dias úteis após aprovação."})
            assert response.status_code == 201, response.text
            result = run(client, headers, "Qual prazo do reembolso?")
            assert result["status"] == "completed", result
            assert result["sources"]
            with app.state.db.sessions() as session:
                assert session.execute(text("SELECT vector_dims(embedding) FROM chunks LIMIT 1")).scalar() == 384
            assert client.get("/api/usage", headers=headers).json()["reserved_tokens"] == 0
            graph = run(client, headers, "Qual prazo do reembolso?", "langgraph", conversation_id="pg-checkpoint", memory_enabled=True)
            assert graph["status"] == "completed", graph
            assert client.delete("/api/conversations/pg-checkpoint", headers=headers).status_code == 200
            usage = client.get("/api/usage", headers=headers).json()
            limits = client.get("/api/settings", headers=headers).json()
            limits.update(tenant_tokens=usage["input_tokens"] + usage["output_tokens"] + 8192, concurrency=10)
            client.put("/api/settings", headers=headers, json=limits)
            def submit(_):
                return client.post("/api/runs", headers=headers, json={"question": "reembolso", "strategy": "async"})
            with ThreadPoolExecutor(max_workers=6) as pool:
                admissions = list(pool.map(submit, range(6)))
            assert sum(a.status_code == 202 for a in admissions) == 2
            assert sum(a.status_code == 429 for a in admissions) == 4
            accepted = [a.json()["id"] for a in admissions if a.status_code == 202]
            client.post(f"/api/runs/{accepted[0]}/cancel", headers=headers)
            # Two workers race to claim one durable job. Exactly one executes.
            with ThreadPoolExecutor(max_workers=2) as pool:
                list(pool.map(app.state.executor.execute, [accepted[1], accepted[1]]))
            executed = client.get(f"/api/runs/{accepted[1]}", headers=headers).json()
            assert executed["status"] == "completed"
            assert sum(e["type"] == "model" for e in executed["events"]) == 1
            ticket_run = run(client, headers, "/ticket Teste atômico", "agent")
            key = ticket_run["approval_id"]
            with ThreadPoolExecutor(max_workers=4) as pool:
                decisions = list(pool.map(lambda _: client.post(f"/api/approvals/{key}/approve", headers=headers, json={}), range(4)))
            assert all(d.status_code == 200 for d in decisions)
            assert len({d.json()["ticket_id"] for d in decisions}) == 1
            assert len(client.get("/api/tickets", headers=headers).json()) == 1

    finally:
        app.state.db.engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()
