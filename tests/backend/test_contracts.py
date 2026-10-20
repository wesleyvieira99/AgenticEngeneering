import math
import pytest

from packages.context.assembly import assemble, estimate_tokens
from packages.contracts.models import StructuredAnswer
from packages.model_gateway.gateway import Gateway
from packages.retrieval.pipeline import embed
from packages.security.auth import password_hash, verify_password
from packages.tools.registry import action_digest


def test_embedding_and_context_bound():
    vector = embed("vetor aprendizagem vetor")
    assert len(vector) == 384
    assert math.isclose(sum(x*x for x in vector), 1)
    assert embed("vetor aprendizagem vetor") == vector
    sources = [{"id": str(i), "text": "texto " * 200, "title": "a", "score": 0.1} for i in range(10)]
    messages, selected = assemble("pergunta", sources, [], [], 3000)
    assert estimate_tokens("".join(m["content"] for m in messages)) <= 3000
    assert len(selected) < len(sources)
    assert "DADOS NÃO CONFIÁVEIS" in messages[0]["content"]


def test_password_tokens_and_exact_digest(app):
    stored = password_hash("test")
    assert verify_password("test", stored)
    assert not verify_password("test1", stored)
    p = app.state.auth.login("acme", "admin", "atlas-local-only")
    token = app.state.auth.issue(p)
    assert app.state.auth.verify(token) == p
    with pytest.raises(Exception):
        app.state.auth.verify(token[:-1] + ("0" if token[-1] != "0" else "1"))
    assert action_digest("acme", "r", "ticket.create", {"title": "A"}) != action_digest("orbit", "r", "ticket.create", {"title": "A"})


def test_bedrock_converse_contract():
    class Client:
        def converse(self, **request):
            assert request["modelId"] == "deterministic-extractive-v1"
            assert request["system"] == [{"text": "trusted"}]
            assert request["messages"] == [{"role": "user", "content": [{"text": "data"}]}]
            assert request["inferenceConfig"] == {"maxTokens": 100, "temperature": 0}
            return {"output": {"message": {"content": [{"text": "ok"}]}}, "usage": {"inputTokens": 4, "outputTokens": 1}}
    result = Gateway().bedrock_converse(Client(), [{"role": "system", "content": "trusted"}, {"role": "user", "content": "data"}], 100)
    assert result["usage"]["inputTokens"] == 4


def test_structured_schema_and_citation_validation():
    with pytest.raises(Exception):
        StructuredAnswer.model_validate({"answer": "ok", "execute_shell": "rm"})
    gateway = Gateway()
    result = gateway.complete([{"role": "user", "content": "x"}], [{"id": "doc", "text": "fonte"}], 100, 1)
    assert result.answer.citation_ids == ["doc"]
    assert result.usage["provider"] == "deterministic"
    assert result.usage["cost_usd"] == 0


def test_partial_json_stream_decoder():
    from packages.model_gateway.gateway import answer_prefix
    assert answer_prefix('{"answer":"Olá ') == "Olá "
    assert answer_prefix('{"answer":"linha\\nseguinte","citation_ids":[') == "linha\nseguinte"
    assert answer_prefix('{"answer":"a\\u00') == "a"
    assert answer_prefix('{"answer":"a\\u00e1') == "aá"
    assert answer_prefix('{"citation_ids":[') == ""


def test_provider_native_stream_contract(monkeypatch):
    from packages.model_gateway import gateway as module
    lifecycle = {"provider_done": False}
    pieces = []
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def raise_for_status(self):
            pass
        def iter_lines(self):
            import json
            for chunk in ('{"answer":"Resposta ', 'com fonte [x]","citation_ids":["x"],"insufficient_evidence":false}'):
                yield json.dumps({"message": {"content": chunk}, "done": False})
            assert len(pieces) == 2, "Token callbacks must occur while the provider iterator is still running"
            lifecycle["provider_done"] = True
            yield json.dumps({"done": True, "prompt_eval_count": 10, "eval_count": 12})
            raise AssertionError("Gateway must stop at terminal usage, without waiting for socket closure")
    def stream(method, url, **kwargs):
        assert kwargs["json"]["stream"] is True
        return Response()
    monkeypatch.setattr(module.httpx, "stream", stream)
    def on_token(piece):
        assert not lifecycle["provider_done"], "Expected incremental callback before terminal provider frame"
        pieces.append(piece)
    result = Gateway("ollama").complete([{"role": "user", "content": "question"}], [{"id": "x"}], 100, 3, on_token=on_token)
    assert lifecycle["provider_done"]
    assert len(pieces) == 2
    assert "".join(pieces) == result.answer.answer
    assert result.usage["input_tokens"] == 10


def test_invalid_provider_citations_fallback_preserves_actual_usage(monkeypatch):
    from packages.model_gateway import gateway as module
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {"message": {"content": '{"answer":"Wrong [stolen]","citation_ids":["stolen"],"insufficient_evidence":false}'}, "prompt_eval_count": 31, "eval_count": 15}
    monkeypatch.setattr(module.httpx, "post", lambda *a, **k: Response())
    result = Gateway("ollama").complete([{"role": "user", "content": "question"}], [{"id": "authorized", "text": "Prazo 7 dias"}], 100, 1)
    assert "stolen" not in result.answer.answer
    assert result.answer.citation_ids == ["authorized"]
    assert result.usage["input_tokens"] == 31
    assert result.usage["validation_fallback"] == "schema_or_citations"


@pytest.mark.parametrize("mode", ["bedrock", "litellm"])
def test_paid_gateway_rejects_zero_prices(monkeypatch, mode):
    monkeypatch.setenv("ATLAS_PRICE_VERSION", "approved-test-price-version")
    monkeypatch.setenv("ATLAS_INPUT_USD_PER_MILLION", "0")
    monkeypatch.setenv("ATLAS_OUTPUT_USD_PER_MILLION", "1")
    with pytest.raises(ValueError, match="positive"):
        Gateway(mode)
    monkeypatch.setenv("ATLAS_INPUT_USD_PER_MILLION", "1")
    monkeypatch.setenv("ATLAS_OUTPUT_USD_PER_MILLION", "0")
    with pytest.raises(ValueError, match="positive"):
        Gateway(mode)


def test_local_empty_price_version_uses_explicit_default(monkeypatch):
    monkeypatch.setenv("ATLAS_PRICE_VERSION", "")
    assert Gateway("deterministic").price_version == "local-zero-inference-v1"


def test_provider_stream_without_final_usage_fails_closed(monkeypatch):
    from packages.model_gateway import gateway as module
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def raise_for_status(self):
            pass
        def iter_lines(self):
            import json
            yield json.dumps({"message": {"content": '{"answer":"Partial response'}, "done": False})
    monkeypatch.setattr(module.httpx, "stream", lambda *a, **k: Response())
    pieces = []
    with pytest.raises(RuntimeError, match="without final usage"):
        Gateway("ollama").complete([{"role": "user", "content": "question"}], [], 100, 3, on_token=pieces.append)
    assert pieces == ["Partial response"]
