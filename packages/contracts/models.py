"""HTTP inputs reject undeclared properties, including attacker supplied tenant IDs."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(StrictModel):
    tenant: str = Field(min_length=1, max_length=64)
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=512)


class DocumentInput(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=1_048_576)


class RunInput(StrictModel):
    question: str = Field(min_length=1, max_length=4000)
    strategy: Literal["baseline", "direct", "rag", "cag", "agent", "langgraph", "multiagent", "async"] = "rag"
    conversation_id: str | None = Field(default=None, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    memory_enabled: bool = False


class Limits(StrictModel):
    tenant_tokens: int = Field(default=100_000, ge=1, le=100_000_000)
    tenant_cost_usd: float = Field(default=10.0, ge=0, le=100_000)
    max_tokens: int = Field(default=4096, ge=256, le=32768)
    max_output_tokens: int = Field(default=512, ge=64, le=4096)
    max_calls: int = Field(default=3, ge=1, le=10)
    max_tools: int = Field(default=3, ge=0, le=10)
    max_steps: int = Field(default=12, ge=2, le=40)
    timeout_seconds: int = Field(default=60, ge=1, le=300)
    concurrency: int = Field(default=4, ge=1, le=32)


class StructuredAnswer(StrictModel):
    answer: str = Field(min_length=1, max_length=40000)
    citation_ids: list[str] = Field(default_factory=list, max_length=20)
    insufficient_evidence: bool = False


class TicketArguments(StrictModel):
    title: str = Field(min_length=1, max_length=200)


class ToolPlan(StrictModel):
    tool_names: list[Literal["documents.search", "tickets.list"]] = Field(default_factory=list, max_length=2)
