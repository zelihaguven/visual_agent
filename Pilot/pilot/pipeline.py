"""Uçtan uca hat: soru_cevapla(). Arayüzden bağımsızdır (Streamlit, test betiği, değerlendirme aynısını çağırır)."""
import json
import time
from dataclasses import dataclass, field
from typing import Any

from .config import MIN_RERANK_SCORE, TOP_K_SOURCES
from .llm import chat_json
from .query import QueryContext, analyze_query
from .retrieve import Hit, search
from .speech import normalize_for_speech
from .verify import Verification, verify

LANG_NAMES = {"en": "EN", "fr": "FR", "es": "ES", "tr": "TR"}


@dataclass
class Result:
    question: str
    context: QueryContext
    hits: list[Hit]
    answer: dict[str, Any]
    verification: Verification
    speech_text: str
    timings: dict[str, float] = field(default_factory=dict)
    llm_called: bool = True

    def source(self, no: int) -> dict[str, Any]:
        return self.hits[no - 1].chunk


def format_sources(hits: list[Hit]) -> str:
    parts = []
    for no, h in enumerate(hits, start=1):
        c = h.chunk
        parts.append(f'<kaynak no="{no}" doküman="{c["doc_id"]}" marka="{c["brand"]}" ürün="{c["product"]}" '
                     f'dil="{LANG_NAMES.get(c["lang"], c["lang"])}" tür="{c["doc_type"]}">\n{c["text"]}\n</kaynak>')
    return "<kaynaklar>\n" + "\n".join(parts) + "\n</kaynaklar>"


def _not_found(question: str, ctx: QueryContext, hits: list[Hit], timings: dict[str, float]) -> Result:
    answer = {"bulunamadi": True, "alintilar": [], "cevap": "", "sesli_metin": "",
              "netlestirme_sorusu": None, "celiski_var": False}
    return Result(question, ctx, hits, answer, verify(answer, {}), "", timings, llm_called=False)


def soru_cevapla(question: str, *, brands: list[str] | None = None, doc_ids: list[str] | None = None,
                 mode: str = "hybrid", query_en: str | None = None) -> Result:
    timings: dict[str, float] = {}
    t0 = time.time()
    ctx = analyze_query(question)
    scope = list(doc_ids) if doc_ids else (list(ctx.doc_ids) or None)

    t = time.time()
    hits = search(question, brands=brands, doc_ids=scope, mode=mode, top_k=TOP_K_SOURCES, query_en=query_en)
    timings["search"] = time.time() - t

    if not hits or (MIN_RERANK_SCORE is not None and hits[0].rerank_score is not None
                    and hits[0].rerank_score < MIN_RERANK_SCORE):
        timings["total"] = time.time() - t0
        return _not_found(question, ctx, hits, timings)

    t = time.time()
    user = f"{format_sources(hits)}\n\n<soru>\n{question}\n</soru>"
    try:
        answer, stats = chat_json(user)
        timings.update({k: float(v) for k, v in stats.items()})
    except json.JSONDecodeError:
        # model JSON'u yarıda bıraktı (token sınırı): cevap güvenilmez, hat çökmez
        timings["llm"] = time.time() - t
        timings["total"] = time.time() - t0
        broken = {"bulunamadi": False, "alintilar": [], "cevap": "", "sesli_metin": "",
                  "netlestirme_sorusu": None, "celiski_var": False}
        bad = Verification("failed", ["Model çıktısı bozuk (JSON tamamlanmadı)"], {})
        return Result(question, ctx, hits, broken, bad, "", timings)
    timings["llm"] = time.time() - t

    t = time.time()
    sources = {no: h.chunk["text"] for no, h in enumerate(hits, start=1)}
    verification = verify(answer, sources)
    timings["verify"] = time.time() - t

    speech = ""
    if verification.status in ("verified", "partial") and answer.get("sesli_metin"):
        speech = normalize_for_speech(answer["sesli_metin"])
    timings["total"] = time.time() - t0
    return Result(question, ctx, hits, answer, verification, speech, timings)
