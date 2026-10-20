import pytest
from fastapi.testclient import TestClient
from services.api.main import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(f"sqlite:///{tmp_path / 'atlas.db'}", "deterministic")


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client


def auth(client, tenant="acme", username="admin"):
    result = client.post("/api/auth/login", json={"tenant": tenant, "username": username, "password": "atlas-local-only"})
    assert result.status_code == 200, result.text
    return {"Authorization": "Bearer " + result.json()["access_token"]}


@pytest.fixture
def headers(client):
    return auth(client)


def run(client, headers, question="Qual é o prazo do reembolso?", strategy="rag", **extra):
    response = client.post("/api/runs", headers=headers, json={"question": question, "strategy": strategy, **extra})
    assert response.status_code == 202, response.text
    return client.get("/api/runs/" + response.json()["id"], headers=headers).json()
