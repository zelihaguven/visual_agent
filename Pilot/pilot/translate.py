"""Sorgu çevirisi, yalnız BM25 kolu için: soru, aranan kapsamdaki parçaların diline çevrilir; dense kollar özgün soruyu
kullanır (çok dilli model). Hedef diller kapsamın kendi parçalarından otomatik (chunk.py'nin tespit ettiği dil; payı en az
MIN_SHARE olanlar), dokümana özgü ayar yok. Kodlar, model numaraları, sayılar ve birimler korunur.
"""
import json
import re
from collections import Counter
from functools import lru_cache
from typing import Any

from .config import CHUNKS_PATH

MIN_SHARE = 0.25
LANG_NAMES = {"en": "English", "tr": "Turkish", "fr": "French", "es": "Spanish", "de": "German", "it": "Italian",
              "pt": "Portuguese"}
PROMPT = ("You translate search queries for a technical document search engine. Translate the user's question from "
          "{src} into: {targets}. Keep product codes, model numbers, error codes, numbers and units exactly as written. "
          "Use the technical terms a manual or specification would use. Reply with a JSON object whose keys are the "
          "language codes ({codes}) and whose values are the translations; nothing else.")


@lru_cache(maxsize=1)
def _doc_lang_counts() -> dict[str, Counter]:
    out: dict[str, Counter] = {}
    if CHUNKS_PATH.exists():
        with CHUNKS_PATH.open(encoding="utf-8") as f:
            for line in f:
                c = json.loads(line)
                out.setdefault(c["doc_id"], Counter())[c["lang"]] += 1
    return out


def target_languages(scope: list[str] | None) -> list[str]:
    """Kapsamdaki parçaların dilleri (payı ≥ MIN_SHARE), en sık önce. Kapsam yoksa bütün korpus."""
    counts = _doc_lang_counts()
    total: Counter = Counter()
    for d in scope or list(counts):
        total.update(counts.get(d, Counter()))
    n = sum(total.values())
    return [lang for lang, k in total.most_common() if n and k / n >= MIN_SHARE] or ["en"]


def translate_query(question: str, src: str, targets: list[str], chat: Any) -> dict[str, str]:
    """{dil: çeviri}; kaynak dil hedeflerdeyse o dil için soru olduğu gibi. Çeviri gerekmiyorsa çağrı yapılmaz."""
    out = {src: question} if src in targets else {}
    need = [t for t in targets if t != src]
    if not need:
        return out
    msg = PROMPT.format(src=LANG_NAMES.get(src, src), targets=", ".join(LANG_NAMES.get(t, t) for t in need),
                        codes=", ".join(need))
    raw = chat.complete([{"role": "system", "content": msg}, {"role": "user", "content": question}], json_mode=True)
    m = re.search(r"\{.*\}", raw, re.S)
    got = json.loads(m.group(0)) if m else {}
    out.update({t: str(got[t]).strip() for t in need if got.get(t)})
    return out


def bm25_text(translations: dict[str, str], fallback: str) -> str:
    """BM25 sorgusu: çevirilerin birleşimi (BM25 kelime torbası: diller birbirini bozmaz). Çeviri yoksa özgün soru."""
    return " ".join(dict.fromkeys(translations.values())) or fallback
