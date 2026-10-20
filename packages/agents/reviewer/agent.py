def review(answer, sources):
    unknown = set(answer.citation_ids) - {s["id"] for s in sources}
    if unknown:
        raise ValueError("Citação fora do contexto autorizado")
    return {"agent": "reviewer", "schema_valid": True, "citations_valid": True, "groundedness": "not_automatically_proven"}
