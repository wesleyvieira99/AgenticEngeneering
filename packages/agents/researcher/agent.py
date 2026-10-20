from packages.retrieval.pipeline import retrieve


def research(db, principal, question):
    return {"agent": "researcher", "sources": retrieve(db, principal.tenant, question), "tool": "documents.search"}
