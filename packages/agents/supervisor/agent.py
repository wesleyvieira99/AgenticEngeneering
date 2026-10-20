from concurrent.futures import ThreadPoolExecutor
from packages.agents.analyst.agent import analyze
from packages.agents.researcher.agent import research


def delegate(db, principal, question):
    """Bounded fan-out/fan-in. Specialists are deterministic, final synthesis uses gateway."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        researcher = pool.submit(research, db, principal, question)
        analyst = pool.submit(analyze, db, principal)
        return researcher.result(), analyst.result()
