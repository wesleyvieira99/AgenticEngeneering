"""One central gateway: no implicit paid fallback, retry or hidden provider call.
A provider timeout is charge-ambiguous; the caller retains its reservation.
"""
import json
import hashlib
import math
import os
import re
from dataclasses import dataclass

import httpx

from packages.context.assembly import estimate_tokens
from packages.contracts.models import StructuredAnswer, ToolPlan


@dataclass
class Completion:
    answer: StructuredAnswer | ToolPlan
    usage: dict


class Gateway:
    def __init__(self, mode=None):
        self.mode = mode or os.getenv("ATLAS_MODE", "deterministic")
        self.model = os.getenv("ATLAS_MODEL", {"deterministic": "deterministic-extractive-v1", "ollama": "qwen2.5:0.5b", "litellm": "configured-by-operator", "bedrock": "amazon.nova-micro-v1:0"}.get(self.mode, "unknown"))
        if self.mode not in {"deterministic", "ollama", "litellm", "bedrock"}:
            raise ValueError("Unknown ATLAS_MODE")
        self.input_price = float(os.getenv("ATLAS_INPUT_USD_PER_MILLION", "0"))
        self.output_price = float(os.getenv("ATLAS_OUTPUT_USD_PER_MILLION", "0"))
        self.price_version = os.getenv("ATLAS_PRICE_VERSION") or "local-zero-inference-v1"
        if min(self.input_price, self.output_price) < 0 or not math.isfinite(self.input_price + self.output_price):
            raise ValueError("Invalid prices")
        if self.mode in {"litellm", "bedrock"}:
            if not os.getenv("ATLAS_PRICE_VERSION") or self.input_price <= 0 or self.output_price <= 0:
                raise ValueError("Paid modes require explicit versioned, positive input/output prices")

    def configuration_snapshot(self):
        """Only safe execution/pricing identifiers; never credentials or provider URLs."""
        from packages.retrieval.pipeline import embedding_version
        configuration = {"mode": self.mode, "model": self.model, "price_version": self.price_version,
                         "input_usd_per_million": self.input_price,
                         "output_usd_per_million": self.output_price,
                         "embedding_version": embedding_version(),
                         "region": os.getenv("AWS_REGION", "us-east-1") if self.mode == "bedrock" else None}
        canonical = json.dumps(configuration, sort_keys=True, separators=(",", ":"))
        return {"configuration": configuration, "sha256": hashlib.sha256(canonical.encode()).hexdigest()}

    def reservation_microdollars(self, tokens):
        return math.ceil(tokens * max(self.input_price, self.output_price))

    def complete(self, messages, sources, max_output, timeout, schema=StructuredAnswer, on_token=None):
        approximate = False
        if self.mode == "deterministic":
            if schema is ToolPlan:
                question = messages[-1]["content"].casefold()
                names = ["documents.search"]
                if "ticket" in question or "chamado" in question:
                    names.append("tickets.list")
                answer = ToolPlan(tool_names=names)
            elif sources:
                chosen = sources[:2]
                text = "Modo determinístico, sem inferência LLM.\n" + "\n".join(f'{s["text"][:220]} [{s["id"]}]' for s in chosen)
                answer = StructuredAnswer(answer=text, citation_ids=[s["id"] for s in chosen])
            else:
                answer = StructuredAnswer(answer="Modo determinístico, sem inferência LLM. Não há evidência documental suficiente para responder.", insufficient_evidence=True)
            raw = answer.model_dump_json()
            input_tokens = min(estimate_tokens(json.dumps(messages)), sum(len(m["content"]) for m in messages))
            output_tokens = min(max_output, max(1, len(raw.encode()) // 3))
            approximate = True
        elif self.mode == "ollama":
            streaming = on_token is not None and schema is StructuredAnswer
            request = {"model": self.model, "messages": messages, "stream": streaming, "format": schema.model_json_schema(), "options": {"num_predict": max_output, "temperature": 0}}
            if streaming:
                raw, emitted, final = "", "", None
                with httpx.stream("POST", os.getenv("ATLAS_OLLAMA_URL", "http://localhost:11434").rstrip("/") + "/api/chat", json=request, timeout=timeout) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue
                        payload = json.loads(line)
                        if payload.get("error"):
                            raise RuntimeError("Ollama streaming error")
                        raw += payload.get("message", {}).get("content", "")
                        preview = answer_prefix(raw)
                        if len(preview) > len(emitted):
                            on_token(preview[len(emitted):])
                            emitted = preview
                        if payload.get("done"):
                            final = payload
                            break  # final usage is terminal; do not wait for socket closure
                if final is None:
                    raise RuntimeError("Provider stream ended without final usage")
                input_tokens, output_tokens = final["prompt_eval_count"], final["eval_count"]
            else:
                response = httpx.post(os.getenv("ATLAS_OLLAMA_URL", "http://localhost:11434").rstrip("/") + "/api/chat", json=request, timeout=timeout)
                response.raise_for_status()
                payload = response.json()
                raw = payload["message"]["content"]
                input_tokens = payload["prompt_eval_count"]
                output_tokens = payload["eval_count"]
        elif self.mode == "litellm":
            # OpenAI-compatible LiteLLM proxy. URL is administrator config, never user input.
            response = httpx.post(os.environ["ATLAS_LITELLM_URL"].rstrip("/") + "/chat/completions", headers={"Authorization": "Bearer " + os.environ["ATLAS_LITELLM_KEY"]}, json={"model": self.model, "messages": messages, "max_tokens": max_output, "temperature": 0, "response_format": {"type": "json_object"}}, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            raw = payload["choices"][0]["message"]["content"]
            input_tokens = payload["usage"]["prompt_tokens"]
            output_tokens = payload["usage"]["completion_tokens"]
        else:
            import boto3
            from botocore.config import Config
            client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"), config=Config(read_timeout=timeout, connect_timeout=min(10, timeout), retries={"total_max_attempts": 1}))
            payload = self.bedrock_converse(client, messages, max_output)
            raw = "".join(part.get("text", "") for part in payload["output"]["message"]["content"])
            input_tokens = payload["usage"]["inputTokens"]
            output_tokens = payload["usage"]["outputTokens"]
        validation_fallback = None
        try:
            answer = schema.model_validate_json(raw)
            allowed = {source["id"] for source in sources}
            if isinstance(answer, StructuredAnswer):
                inline = set(re.findall(r"\[([a-zA-Z0-9_-]{1,64})\]", answer.answer))
                if set(answer.citation_ids) - allowed or inline - allowed:
                    raise ValueError("Unknown citation")
                if sources and not answer.insufficient_evidence and not answer.citation_ids:
                    raise ValueError("Grounded answer requires citations")
                for citation in answer.citation_ids:
                    if f"[{citation}]" not in answer.answer:
                        answer.answer += f" [{citation}]"
        except ValueError:
            if schema is not StructuredAnswer:
                raise
            validation_fallback = "schema_or_citations"
            chosen = sources[:2]
            answer = StructuredAnswer(answer="Validação da resposta do modelo falhou. Trechos autorizados: " + ("\n".join(f'{item["text"][:220]} [{item["id"]}]' for item in chosen) if chosen else "Não há evidência suficiente."), citation_ids=[item["id"] for item in chosen], insufficient_evidence=not bool(chosen))
        usage = {"input_tokens": input_tokens, "output_tokens": output_tokens, "cost_usd": (input_tokens * self.input_price + output_tokens * self.output_price) / 1_000_000, "model": self.model, "provider": self.mode, "price_version": self.price_version, "estimated_tokens": approximate, "validation_fallback": validation_fallback}
        return Completion(answer, usage)

    def bedrock_converse(self, client, messages, max_output):
        return client.converse(modelId=self.model, system=[{"text": m["content"]} for m in messages if m["role"] == "system"], messages=[{"role": m["role"], "content": [{"text": m["content"]}]} for m in messages if m["role"] != "system"], inferenceConfig={"maxTokens": max_output, "temperature": 0})


def answer_prefix(raw):
    """Extract only complete JSON string code points from a partial answer field.
    Streamed text is provisional until the full structured object validates.
    """
    match = re.search(r'"answer"\s*:\s*"', raw)
    if not match:
        return ""
    content = raw[match.end():]
    escaped = False
    end = len(content)
    for index, char in enumerate(content):
        if char == '"' and not escaped:
            end = index
            break
        if char == "\\" and not escaped:
            escaped = True
        else:
            escaped = False
    candidate = content[:end]
    # A partial escape sequence at chunk boundary must wait for the next chunk.
    for trim in range(min(6, len(candidate)) + 1):
        value = candidate[:len(candidate) - trim] if trim else candidate
        try:
            return json.loads('"' + value + '"')
        except json.JSONDecodeError:
            continue
    return ""
