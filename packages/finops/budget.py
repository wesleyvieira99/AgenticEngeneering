"""Admission reserves token/cost headroom in the same transaction as a new run.
Never release ambiguous provider calls on timeout. Reconciliation is idempotent.
"""
import math
from fastapi import HTTPException
from services.api.db import Tenant


def reserve(session, run, gateway):
    tenant = session.get(Tenant, run.tenant)
    limits = tenant.limits
    amount = limits["max_tokens"]
    cost = gateway.reservation_microdollars(amount)
    if tenant.active_runs >= limits["concurrency"]:
        raise HTTPException(429, "Limite de concorrência do tenant atingido")
    if tenant.used_tokens + tenant.reserved_tokens + amount > limits["tenant_tokens"]:
        raise HTTPException(429, "Orçamento global de tokens insuficiente")
    if tenant.used_microdollars + tenant.reserved_microdollars + cost > round(limits["tenant_cost_usd"] * 1_000_000):
        raise HTTPException(429, "Orçamento global de custo insuficiente")
    tenant.reserved_tokens += amount
    tenant.reserved_microdollars += cost
    tenant.active_runs += 1
    run.reserved_tokens = amount
    run.reserved_microdollars = cost
    run.reservation_open = True
    run.limits = dict(limits)
    run.checkpoint = {**(run.checkpoint or {}), "gateway_snapshot": gateway.configuration_snapshot()}


def reconcile(session, run, usage):
    if not run.reservation_open:
        return
    tenant = session.get(Tenant, run.tenant)
    tenant.reserved_tokens -= run.reserved_tokens
    tenant.reserved_microdollars -= run.reserved_microdollars
    tenant.active_runs -= 1
    tenant.used_tokens += usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
    tenant.used_microdollars += math.ceil(usage.get("cost_usd", 0) * 1_000_000)
    run.reservation_open = False


def release_unstarted(session, run):
    reconcile(session, run, {})
