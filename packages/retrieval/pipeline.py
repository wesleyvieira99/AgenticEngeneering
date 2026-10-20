"""Tenant-filtered hybrid BM25 + vector search with reciprocal rank fusion.
Hash embeddings are deterministic test features, NOT semantic model embeddings.
"""
import hashlib
import math
import os

import httpx
import re
import unicodedata
from collections import Counter

from fastapi import HTTPException
from sqlalchemy import delete, select

from services.api.db import Chunk, ContextCache, Document, Tenant, now, uid

EMBEDDING_DIMENSION = 384


def embedding_version():
    mode = os.getenv("ATLAS_EMBEDDING_MODE", "hash")
    if mode == "hash":
        return "hash-384-v1"
    if mode == "ollama":
        return "ollama:" + os.getenv("ATLAS_EMBEDDING_MODEL", "all-minilm") + ":384"
    raise ValueError("Unknown ATLAS_EMBEDDING_MODE")


def terms(text):
    text = unicodedata.normalize("NFKD", text.casefold())
    raw = re.findall(r"\w+", "".join(c for c in text if not unicodedata.combining(c)))
    stopwords = {"a", "o", "e", "as", "os", "de", "do", "da", "dos", "das", "que", "qual", "quais", "em", "um", "uma", "para", "por", "como", "se", "no", "na", "ao", "aos", "com", "quando", "pode", "fazer", "ser", "sao", "eh"}
    return [term[:-1] if len(term) > 4 and term.endswith("s") else term for term in raw if term not in stopwords]


def embed(text):
    if os.getenv("ATLAS_EMBEDDING_MODE", "hash") == "ollama":
        response = httpx.post(os.getenv("ATLAS_OLLAMA_URL", "http://localhost:11434").rstrip("/") + "/api/embed", json={"model": os.getenv("ATLAS_EMBEDDING_MODEL", "all-minilm"), "input": text, "truncate": False}, timeout=60)
        response.raise_for_status()
        vector = response.json()["embeddings"][0]
        if len(vector) != EMBEDDING_DIMENSION or any(not math.isfinite(x) for x in vector):
            raise ValueError("Embedding dimension/model mismatch; expected 384 finite dimensions")
        return vector
    if os.getenv("ATLAS_EMBEDDING_MODE", "hash") != "hash":
        raise ValueError("Unknown embedding mode")
    vector = [0.0] * EMBEDDING_DIMENSION
    for term, count in Counter(terms(text)).items():
        digest = hashlib.sha256(term.encode()).digest()
        vector[int.from_bytes(digest[:2], "big") % EMBEDDING_DIMENSION] += count * (1 if digest[2] % 2 else -1)
    norm = math.sqrt(sum(x * x for x in vector)) or 1
    return [x / norm for x in vector]


def chunk_text(text, size=650, overlap=100):
    """Character windows preserve offsets conceptually; no semantic chunking claim."""
    text = unicodedata.normalize("NFC", text.replace("\r\n", "\n")).strip()
    return [text[start:start + size] for start in range(0, len(text), size - overlap)]


def ingest(db, tenant, title, content):
    if len(content.encode()) > 1_048_576:
        raise HTTPException(413, "Documento excede 1 MiB")
    normalized = unicodedata.normalize("NFC", content.replace("\r\n", "\n")).strip()
    digest = hashlib.sha256(normalized.encode()).hexdigest()
    parts = chunk_text(normalized)
    vectors = [embed(part) for part in parts]
    with db.transaction(tenant) as s:
        duplicate = s.scalar(select(Document).where(Document.tenant == tenant, Document.content_hash == digest))
        if duplicate:
            return document_dict(duplicate)
        versions = s.scalars(select(Document.version).where(Document.tenant == tenant, Document.title == title)).all()
        doc = Document(id=uid(), tenant=tenant, title=title, content_hash=digest, version=max(versions, default=0) + 1)
        s.add(doc)
        s.flush()
        for pos, (text, vector) in enumerate(zip(parts, vectors)):
            s.add(Chunk(tenant=tenant, document_id=doc.id, position=pos, text=text, embedding=vector, embedding_model=embedding_version()))
        s.get(Tenant, tenant).corpus_version += 1
        s.execute(delete(ContextCache).where(ContextCache.tenant == tenant))
        s.flush()
        return document_dict(doc)


def document_dict(doc):
    return {"id": doc.id, "title": doc.title, "version": doc.version, "created_at": doc.created_at}


def source(chunk, doc, score=0.0):
    return {"id": chunk.id, "title": doc.title, "text": chunk.text, "score": round(score, 6)}


def retrieve(db, tenant, query, limit=5):
    with db.sessions() as s:
        rows = s.execute(select(Chunk, Document).join(Document).where(Chunk.tenant == tenant, Document.tenant == tenant)).all()
        if not rows:
            return []
        if any(c.embedding_model != embedding_version() for c, _ in rows):
            raise HTTPException(409, "Modelo de embedding mudou; execute POST /api/documents/reindex")
        query_terms = terms(query)
        tokenized = [terms(c.text) for c, _ in rows]
        average = sum(map(len, tokenized)) / len(rows)
        bm = []
        for (c, d), tokens in zip(rows, tokenized):
            counts = Counter(tokens)
            score = 0.0
            for term in query_terms:
                df = sum(term in other for other in tokenized)
                idf = math.log(1 + (len(rows) - df + 0.5) / (df + 0.5))
                freq = counts[term]
                score += idf * freq * 2.2 / (freq + 1.2 * (0.25 + 0.75 * len(tokens) / average))
            bm.append((c.id, score))
        qvec = embed(query)
        if db.engine.dialect.name == "postgresql":
            vector_ids = list(s.scalars(select(Chunk.id).where(Chunk.tenant == tenant).order_by(Chunk.embedding.cosine_distance(qvec)).limit(max(20, limit))))
        else:
            vector_ids = [c.id for c, _ in sorted(rows, key=lambda row: -sum(a * b for a, b in zip(row[0].embedding, qvec)))][:max(20, limit)]
        candidates = [source(c, d) for c, d in rows]
        supported = {item["id"] for item in relevant_cached(candidates, query)}
        if os.getenv("ATLAS_EMBEDDING_MODE", "hash") == "ollama":
            threshold = float(os.getenv("ATLAS_MIN_SEMANTIC_SIMILARITY", "0.45"))
            supported.update(c.id for c, _ in rows if sum(a * b for a, b in zip(c.embedding, qvec)) >= threshold)
        positive = supported
        # In hash mode, require lexical evidence to avoid claims based on hash collisions.
        lexical_ids = [cid for cid, _ in sorted(bm, key=lambda x: -x[1]) if cid in positive]
        fused = Counter()
        for ranking in (lexical_ids, vector_ids):
            for rank, cid in enumerate(ranking, 1):
                if cid in positive:
                    fused[cid] += 1 / (60 + rank)
        lookup = {c.id: (c, d) for c, d in rows}
        return [source(*lookup[cid], score) for cid, score in fused.most_common(limit)]


def relevant_cached(sources, query):
    """Generic weighted lexical coverage guard; not a probability of correctness.
    Unseen query terms carry high IDF; generic/shared words cannot dominate support.
    The small threshold is an explicit heuristic requiring evaluation per corpus.
    """
    query_terms = set(terms(query))
    if not query_terms or not sources:
        return []
    corpus = [set(terms(item["text"])) for item in sources]
    weights = {term: max(1.0, math.log(1 + (len(corpus) - sum(term in doc for doc in corpus) + 0.5) / (sum(term in doc for doc in corpus) + 0.5))) for term in query_terms}
    total = sum(weights.values())
    ranked = []
    for item, document in zip(sources, corpus):
        coverage = sum(weight for term, weight in weights.items() if term in document) / total
        if coverage >= float(os.getenv("ATLAS_MIN_LEXICAL_COVERAGE", "0.30")):
            ranked.append((coverage, item))
    return [item for _, item in sorted(ranked, key=lambda pair: -pair[0])]


def cached_corpus(db, tenant):
    """CAG variant: tenant/version keyed preloaded source context; no provider KV cache."""
    with db.transaction(tenant) as s:
        version = s.get(Tenant, tenant).corpus_version
        key = f"{tenant}:{version}:{embedding_version()}"
        cache = s.get(ContextCache, key)
        if cache and cache.expires_at > now():
            return cache.chunks, True
        rows = s.execute(select(Chunk, Document).join(Document).where(Chunk.tenant == tenant, Document.tenant == tenant).order_by(Document.id, Chunk.position).limit(25)).all()
        if len(rows) > 24:
            raise HTTPException(422, "CAG suporta até 24 chunks; use RAG ou reduza o corpus")
        chunks = [source(c, d) for c, d in rows]
        if cache:
            s.delete(cache)
            s.flush()
        s.add(ContextCache(key=key, tenant=tenant, corpus_version=version, chunks=chunks, expires_at=now() + 300))
        return chunks, False


def reindex(db, tenant):
    """Explicit embedding migration; compute outside locks, then compare corpus version."""
    with db.sessions() as s:
        version = s.get(Tenant, tenant).corpus_version
        chunks = s.scalars(select(Chunk).where(Chunk.tenant == tenant)).all()
    vectors = {c.id: embed(c.text) for c in chunks}
    with db.transaction(tenant) as s:
        current = s.get(Tenant, tenant)
        if current.corpus_version != version:
            raise HTTPException(409, "Corpus mudou durante reindexação; repita")
        for cid, vector in vectors.items():
            chunk = s.get(Chunk, cid)
            chunk.embedding, chunk.embedding_model = vector, embedding_version()
        current.corpus_version += 1
        s.execute(delete(ContextCache).where(ContextCache.tenant == tenant))
    return {"reindexed": len(vectors), "embedding_model": embedding_version()}
