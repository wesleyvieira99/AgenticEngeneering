"""Durable SQL queue worker; atomic claim supports multiple processes.
Running jobs abandoned by a worker fail closed; ambiguous spend remains reserved.
"""
import argparse
import time
from sqlalchemy import select
from packages.orchestration.engine import Executor
from packages.observability.tracing import configure
from services.api.db import Database, Run, now


def run_once(db):
    configure()
    with db.sessions() as s:
        rows = s.scalars(select(Run).where(Run.status == "queued").order_by(Run.created_at).limit(20)).all()
        expired = s.scalars(select(Run).where(Run.status == "running")).all()
    for run in expired:
        if run.started_at and now() - run.started_at > run.limits["timeout_seconds"] + 30:
            with db.transaction(run.tenant) as s:
                current = s.get(Run, run.id)
                if current.status == "running":
                    current.status = "failed"
                    current.error = "Worker lease expirou; reserva mantida até reconciliação operacional"
                    db.add_event(s, current, "error", {"message": current.error})
    executor = Executor(db)
    for run in rows:
        executor.execute(run.id)
    return len(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    db = Database()
    db.initialize()
    while True:
        run_once(db)
        if args.once:
            break
        time.sleep(0.5)


if __name__ == "__main__":
    main()
