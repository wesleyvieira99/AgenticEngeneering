"""Explicit specialist contracts. No specialist can bypass the shared run budget."""
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentSpec:
    name: str
    responsibility: str
    allowed_tools: tuple[str, ...]
    done_when: str
    max_delegations: int = 0


SPECS = {
    "supervisor": AgentSpec("supervisor", "Route a task to at most two specialists and aggregate evidence", (), "Both bounded outputs are collected", 2),
    "researcher": AgentSpec("researcher", "Retrieve tenant-authorized evidence", ("documents.search",), "At most five sources with IDs"),
    "analyst": AgentSpec("analyst", "Report authorized ticket counts and states", ("tickets.list",), "A bounded factual summary"),
    "executor": AgentSpec("executor", "Prepare a typed ticket action for human approval", ("tickets.propose",), "An approval digest is persisted"),
    "reviewer": AgentSpec("reviewer", "Validate schema and citation membership", (), "No unknown citation ID is present"),
}
