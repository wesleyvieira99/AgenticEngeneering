"""Operator-only CLI to resolve a charge-ambiguous reservation using provider evidence.
No automatic zero-cost release. Database credentials, not an end-user token, required.
"""
import argparse
import math
from packages.finops.budget import reconcile
from services.api.db import Database, Run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    parser.add_argument("--input-tokens", type=int, required=True)
    parser.add_argument("--output-tokens", type=int, required=True)
    parser.add_argument("--cost-usd", type=float, required=True)
    parser.add_argument("--evidence-id", required=True, help="Provider request/invoice reference; no secrets")
    args = parser.parse_args()
    if min(args.input_tokens, args.output_tokens, args.cost_usd) < 0 or not math.isfinite(args.cost_usd):
        parser.error("Usage must be nonnegative and finite")
    db = Database()
    with db.sessions() as s:
        run = s.get(Run, args.run_id)
        if not run:
            parser.error("Run not found")
        tenant = run.tenant
    with db.transaction(tenant) as s:
        run = s.get(Run, args.run_id)
        if run.status not in {"failed", "cancelled"}:
            parser.error("Only failed/cancelled runs may be reconciled manually")
        if not run.reservation_open:
            print("Already reconciled; no changes")
            return
        usage = dict(run.usage, input_tokens=args.input_tokens, output_tokens=args.output_tokens, cost_usd=args.cost_usd)
        reconcile(s, run, usage)
        run.usage = usage
        db.add_event(s, run, "reconciliation", {"evidence_id": args.evidence_id[:200], "usage": usage, "actor": "database-operator"})
    print("Reservation reconciled with supplied provider evidence")


if __name__ == "__main__":
    main()
