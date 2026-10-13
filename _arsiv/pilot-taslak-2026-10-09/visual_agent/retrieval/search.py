"""Sorgu analizi + yetki filtresi + hibrit arama (dense + BM25, RRF) + rerank + eşik."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from ..config import SETTINGS, load_documents
from ..security import User, access_filter
from . import models
from .index import DENSE, SPARSE, client
from .text import query_vector, tokenize_query, tr_lower

# Ürün ve marka eşanlamlıları (pilot). Gerçek veride doküman metadata'sından ve bir sözlükten gelir.
PRODUCT_ALIASES = {
    "Ceket": ["ceket", "coat", "mont"],
    "Pantolon": ["pantolon", "trouser", "trousers", "pants"],
    "Kahve makinesi": ["kahve makine", "coffee maker", "coffeemaker"],
}
BRAND_ALIASES = {
    "GL-PD": ["gl-pd", "glpd", "gl pd"],
    "Brother": ["brother"],
    "MrCoffee": ["mr. coffee", "mr coffee", "mrcoffee"],
}


@dataclass
class QueryAnalysis:
    models: list[str] = field(default_factory=list)
    products: list[str] = field(default_factory=list)
    brands: list[str] = field(default_factory=list)
    ambiguous_model: str | None = None      # "S-7300" gibi harfsiz model: hangi varyant?


@dataclass
class Hit:
    chunk: dict
    rrf: float
    rerank: float | None = None

    @property
    def score(self) -> float:
        return self.rerank if self.rerank is not None else self.rrf


@dataclass
class SearchResult:
    analysis: QueryAnalysis
    hits: list[Hit]
    found: bool
    reason: str = ""
    timings: dict = field(default_factory=dict)


def _compact(s: str) -> str:
    return re.sub(r"[\s\-_.]", "", s).upper()


def analyze(question: str) -> QueryAnalysis:
    docs = load_documents().values()
    q_low = tr_lower(question)
    q_comp = _compact(question)
    qa = QueryAnalysis()
    for m in sorted({d.product_model for d in docs if d.product_model}):
        if _compact(m) in q_comp:
            qa.models.append(m)
    if not qa.models:
        # Model ailesi yazılmış ama varyant yok ("S-7300"): netleştirme gerekir
        fams = {re.sub(r"[A-Z]$", "", _compact(m)) for d in docs if (m := d.product_model)}
        for f in fams:
            if re.search(rf"{re.escape(f)}(?![A-Z0-9])", q_comp):
                qa.ambiguous_model = f
    for prod, aliases in PRODUCT_ALIASES.items():
        if any(a in q_low for a in aliases):
            qa.products.append(prod)
    for brand, aliases in BRAND_ALIASES.items():
        if any(a in q_low for a in aliases):
            qa.brands.append(brand)
    return qa


def _entity_conditions(qa: QueryAnalysis) -> list:
    from qdrant_client import models as qm
    must = []
    if qa.models:
        must.append(qm.FieldCondition(key="product_model", match=qm.MatchAny(any=qa.models)))
    if qa.products:
        must.append(qm.FieldCondition(key="product", match=qm.MatchAny(any=qa.products)))
    return must


def search(question: str, user: User, selected_brands: list[str] | None = None, top_k: int | None = None,
           use_rerank: bool | None = None, mode: str = "hybrid") -> SearchResult:
    """mode: hybrid | dense | sparse (değerlendirmede karşılaştırma için)."""
    from qdrant_client import models as qm
    top_k = top_k or SETTINGS.top_k
    use_rerank = SETTINGS.rerank_enabled if use_rerank is None else use_rerank
    t = {}
    t0 = time.perf_counter()
    qa = analyze(question)
    # Sorudaki marka, arayüz seçimiyle aynı kuralla (sadece daraltır) uygulanır
    sel = selected_brands or qa.brands or None
    if selected_brands and qa.brands:
        sel = [b for b in selected_brands if b in qa.brands] or selected_brands
    flt = access_filter(user, sel, extra_must=_entity_conditions(qa))

    dense_vec = models.embed([question])[0]
    t["embed"] = time.perf_counter() - t0
    idx, val = query_vector(tokenize_query(question))
    sparse = qm.SparseVector(indices=idx, values=val)

    t1 = time.perf_counter()
    n = SETTINGS.candidates
    if mode == "dense":
        pts = client().query_points(SETTINGS.collection, query=dense_vec, using=DENSE, query_filter=flt,
                                    limit=n, with_payload=True).points
    elif mode == "sparse":
        pts = client().query_points(SETTINGS.collection, query=sparse, using=SPARSE, query_filter=flt,
                                    limit=n, with_payload=True).points
    else:
        pts = client().query_points(
            SETTINGS.collection,
            prefetch=[qm.Prefetch(query=dense_vec, using=DENSE, filter=flt, limit=n),
                      qm.Prefetch(query=sparse, using=SPARSE, filter=flt, limit=n)],
            query=qm.FusionQuery(fusion=qm.Fusion.RRF), limit=n, with_payload=True).points
    t["search"] = time.perf_counter() - t1
    hits = [Hit(chunk=p.payload, rrf=float(p.score)) for p in pts]

    if not hits:
        reason = "Yetkili dokümanlarda eşleşme yok"
        if qa.models or qa.products or qa.brands:
            reason += " (sorudaki model/ürün/marka için doküman bulunamadı veya yetki yok)"
        return SearchResult(qa, [], False, reason, t)

    if use_rerank:
        t2 = time.perf_counter()
        cand = hits[: SETTINGS.rerank_top_n]
        scores = models.rerank_scores(question, [h.chunk["text"][:1500] for h in cand])
        for h, s in zip(cand, scores):
            h.rerank = s
        hits = sorted(cand, key=lambda h: h.rerank, reverse=True)
        t["rerank"] = time.perf_counter() - t2
        best = hits[0].rerank
        found = best >= SETTINGS.threshold
        reason = "" if found else f"En iyi alaka skoru ({best:.2f}) eşiğin ({SETTINGS.threshold:.2f}) altında"
    else:
        found = hits[0].rrf >= SETTINGS.threshold_rrf
        reason = "" if found else "Skor eşiğin altında"
    t["total_search"] = time.perf_counter() - t0
    return SearchResult(qa, hits[:top_k], found, reason, t)
