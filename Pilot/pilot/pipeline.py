"""Uçtan uca hat: soru_cevapla(). Arayüzden bağımsızdır (Streamlit, test betiği, değerlendirme aynısını çağırır)."""
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any

from .chunk import read_chunks
from . import config
from .config import (CHUNKS_PATH, CLARIFY_DOC_RATIO, CLARIFY_METHOD, CLARIFY_MIN_SCORE, MIN_RERANK_SCORE,
                     TOP_K_SOURCES)
from .llm import chat_json
from .query import (CODE_IN_TEXT, MUST_MATCH, QueryContext, analyze_query, asks_nothing_specific, code_key,
                    context_entities, missing_entities, normalize_codes, question_lang,
                    source_aliases, spoken_codes, strip_source_phrases, strip_terms)
from .registry import BY_ID, DOCS, visible
from .retrieve import FUSED_K, Hit, search
from .speech import normalize_for_speech, normalize_for_speech_en
from .tables import record_keys, variant_check
from .terms import expand_query
from .verify import Verification, clarify_options, verify

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
    expanded_terms: list[str] = field(default_factory=list)   # terim sözlüğünden aramaya eklenen kılavuz terimleri
    context_terms: list[str] = field(default_factory=list)    # seçilen kaynak için bağlam: aramadan ve modelden çıkarıldı
    lang: str = "tr"                                          # sorunun ve cevabın dili (ses de bu dilde)

    def source(self, no: int) -> dict[str, Any]:
        return self.hits[no - 1].chunk


def format_sources(hits: list[Hit]) -> str:
    parts = []
    for no, h in enumerate(hits, start=1):
        c = h.chunk
        # Bölüm başlığı da verilir: Aynı metin farklı bölümlerde geçebiliyor (ör. S-7300A'da "Sewing speed 220-3000"
        # hem başlangıç hem bitiş geri dikiş ayarında). Başlık olmadan model hangisinin soruya uyduğunu ayıramıyor.
        section = (c.get("section") or "").replace('"', "'")
        figure = ' parça="şekil"' if c.get("chunk_type") == "figure" else ""
        parts.append(f'<kaynak no="{no}" doküman="{c["doc_id"]}" marka="{c["brand"]}" ürün="{c["product"]}" '
                     f'dil="{LANG_NAMES.get(c["lang"], c["lang"])}" tür="{c["doc_type"]}"{figure} bölüm="{section}">\n'
                     f'{c["text"]}\n</kaynak>')
    return "<kaynaklar>\n" + "\n".join(parts) + "\n</kaynaklar>"


def _not_found(question: str, ctx: QueryContext, hits: list[Hit], timings: dict[str, float],
               reason: str = "", suggest: list[str] | None = None) -> Result:
    """suggest: bilginin bulunabileceği doğru kaynaklar (arayüz 'bu kaynakta ara' düğmesi gösterir)."""
    answer = {"bulunamadi": True, "alintilar": [], "cevap": "", "sesli_metin": "",
              "netlestirme_sorusu": None, "celiski_var": False, "neden": reason, "oneri": suggest or []}
    return Result(question, ctx, hits, answer, verify(answer, {}), "", timings, llm_called=False)


def _clarify(question: str, ctx: QueryContext, timings: dict[str, float], docs: list[str], message: str,
             hits: list[Hit] | None = None, aspects: list[tuple[str, str]] | None = None, hint: str = "",
             llm_called: bool = False) -> Result:
    """Seçenekler iki türlü: kaynak seçimi {"doc_id"} ya da soruya eklenecek konu {"ek"} (soru bir şey sormuyorsa).
    hint: kullanıcının kendisi ayrıntı yazması için örnek."""
    options = ([{"doc_id": d, "etiket": BY_ID[d].product} for d in docs]
               + [{"ek": phrase, "etiket": label} for label, phrase in aspects or []])
    answer = {"bulunamadi": False, "alintilar": [], "cevap": "", "sesli_metin": "",
              "netlestirme_sorusu": message, "celiski_var": False, "secenekler": options, "ipucu": hint}
    return Result(question, ctx, hits or [], answer, Verification("clarify", [], {}), "", timings,
                  llm_called=llm_called)


def _noop(_: str) -> None:
    pass


def _product_in_translation() -> bool:
    """K7 ölçüm seçeneği (PILOT_K7_TRANSLATED): çevrilmiş soruda (ikili yol) belge kaydının ürün adı geçiyor mu.
    Geçiyorsa soru ürünü söylüyor demektir; K7 sormaz."""
    if not config.K7_TRANSLATED:
        return False
    from .query import _squash
    from .registry import product_names
    from .retrieve import last_translation
    text = _squash(last_translation.get("metin") or "")
    return bool(text) and any(_squash(n) in text for d in DOCS for n in product_names(d))


# ---------- c kipi: bulut cevap modeli, şema c150b-J (Adım 2 planı §29) ----------

_CLIENTS: dict[str, Any] = {}
SERVICE_DOWN = ("Cevap servisi şu an kullanılamıyor. Biraz sonra yeniden deneyin. Bulunan kaynak sayfaları aşağıda; "
                "değerleri kaynaktan kontrol edin.")


def _answer_client() -> Any:
    if "answer" not in _CLIENTS:
        from .cloud import AnswerClient
        from .schema_c import schema_variant
        schema, prompt = schema_variant(config.ANSWER_SCHEMA_VARIANT)
        _CLIENTS["answer"] = AnswerClient(config.ANSWER_MODEL, config.ANSWER_PROVIDERS, schema, config.ANSWER_MAX_TOKENS,
                                         config.ANSWER_FIRST_TOKEN_S, config.STREAM_GUARD_N)
        _CLIENTS["prompt"] = prompt
    return _CLIENTS["answer"]


def chat_c(user: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Şema C cevabı ve çağrı kaydı (sağlayıcı, denemeler, ilk token, akış zaman çizelgesi, maliyet). JSON okunamazsa
    ModelJSONError; servise ulaşılamazsa cloud.ServiceUnavailable. Testler bu fonksiyonu değiştirir."""
    from .jsonparse import ModelJSONError, error_detail
    from .schema_c import parse_c
    client = _answer_client()
    rec = client.stream([{"role": "system", "content": _CLIENTS["prompt"]}, {"role": "user", "content": user}])
    ans, status = parse_c(rec["content"], rec.get("finish"))
    if status in ("bos", "kesik", "gecersiz") or ans is None:
        raise ModelJSONError(status == "kesik", error_detail(rec["content"] or "") or status)
    return ans, rec


def _translator(query: str, scope: list[str] | None) -> Any:
    """BM25 sorgu metnini veren çağrı (ikili yol). İstemci kurulamazsa (anahtar yok, ZDR) None: BM25 çevirisiz."""
    from .translate import bm25_text, target_languages, translate_query
    if "translate" not in _CLIENTS:
        try:
            from .cloud import CloudChat
            _CLIENTS["translate"] = CloudChat(config.TRANSLATE_MODEL, timeout=15, providers=config.TRANSLATE_PROVIDERS,
                                              reasoning={"enabled": False})
        except Exception:  # noqa: BLE001
            _CLIENTS["translate"] = None
    chat = _CLIENTS["translate"]
    if chat is None:
        return None
    src, targets = question_lang(query), target_languages(scope)
    if all(t == src for t in targets):
        return None
    return lambda: bm25_text(translate_query(query, src, targets, chat), query)


_CHUNKS: dict[str, Any] = {"mtime": None, "all": [], "rows": {}}


def _chunks() -> dict[str, Any]:
    """Parça dosyası (bellekte); yeniden indekslemeyle dosya değişince yeniden okunur."""
    mtime = CHUNKS_PATH.stat().st_mtime if CHUNKS_PATH.exists() else None
    if _CHUNKS["mtime"] != mtime:
        allc = read_chunks() if mtime else []
        rows: dict[tuple, list[str]] = {}
        for c in allc:
            if c.get("chunk_type") == "table_row":
                rows.setdefault((c["doc_id"], c["page"], c["section"]), []).append(c["text"])
        _CHUNKS.update(mtime=mtime, all=allc, rows=rows)
    return _CHUNKS


def table_siblings(chunk: dict[str, Any]) -> list[str]:
    """Aynı tablonun satırları (aynı doküman, sayfa, bölüm ve sütunlar): satır varyantı kontrolü için."""
    keys = record_keys(chunk["text"])
    same = _chunks()["rows"].get((chunk["doc_id"], chunk["page"], chunk.get("section", "")), [])
    return [t for t in same if keys and record_keys(t) == keys]


# Tanımlayıcı kod: harf + rakam, tiresiz (E050, E07, P41). Model adları tireli ("S-7300A", "MO-6800S") ve doküman
# kaydından eşleşiyor. 2026-10-16 J9: "MO-6800S'te E050" sorusunda arama E05 satırını getirdi, model E05'i anlattı.
CODE_TOKEN_RE = re.compile(r"(?<![\w-])([A-Za-z]{1,3}\d{2,5})(?![\w-])")


def _has_code(text: str, code: str) -> bool:
    """Kod anahtarıyla (query.code_key): tire/boşluk ve baştaki sıfır farkı yok sayılır ("E50" = "E-050" = "E050"),
    sayısal değer farklıysa kod farklıdır ("E05" ≠ "E050")."""
    key = code_key(code)
    if key is None:
        return re.search(rf"(?<![\w-]){re.escape(code)}(?![\w-])", text, re.I) is not None
    return any((m.group(1).upper(), int(m.group(2))) == key for m in CODE_IN_TEXT.finditer(text))


def code_lookup(question: str, scope: list[str] | None, brands: list[str] | None, access: list[str] | None = None
                ) -> tuple[list[dict[str, Any]], list[str], dict[str, list[str]]]:
    """Sorudaki kodlar için kapsamda birebir geçen parçalar, kapsamda hiç geçmeyen kodlar ve bu kodların geçtiği
    kapsam dışı dokümanlar. Arama benzer kodu (E05 ~ E050) getirebiliyor; kod birebir aranır.
    access: kullanıcının yetki grupları; yetkisiz dokümanların parçaları ve adları hiç dönmez (arama gibi)."""
    from .registry import product_names
    aliases = ({a for d in DOCS for a in d.aliases} if config.HAND_LISTS       # tiresiz model adı ("s7300a") kod değil
               else {re.sub(r"[-\s]", "", a) for d in DOCS for a in product_names(d)})
    codes = list(dict.fromkeys(m.group(1).upper() for m in CODE_TOKEN_RE.finditer(question)
                               if m.group(1).lower() not in aliases))
    found: list[dict[str, Any]] = []
    missing: list[str] = []
    elsewhere: dict[str, list[str]] = {}
    for code in codes:
        hits = [c for c in _chunks()["all"] if visible(c["doc_id"], access) and _has_code(c["text"], code)]
        inside = [c for c in hits if (not scope or c["doc_id"] in scope) and (not brands or c["brand"] in brands)]
        if inside:
            # Önce tablo satırı (kod tablosu), sonra metin; kod başına en fazla 2 parça
            found += sorted(inside, key=lambda c: c.get("chunk_type") != "table_row")[:2]
        else:
            missing.append(code)
            elsewhere[code] = list(dict.fromkeys(c["doc_id"] for c in hits))
    return found, missing, elsewhere


def interchangeable(d1: str, d2: str) -> bool:
    """Birbirinin yerine geçebilecek kaynaklar: iki ürün şartnamesi (makine ailesi kuralı 2026-11-05'te silindi)."""
    if d1 == d2:
        return False
    return BY_ID[d1].doc_type == BY_ID[d2].doc_type == "product_standard"


def doc_scores(hits: list[Hit]) -> list[tuple[str, float]]:
    """Adayların füzyon skorları dokümana göre toplanır (skor yoksa sıradan RRF payı: 1/(sıra+2)). Azalan sırada."""
    tot: dict[str, float] = {}
    for i, h in enumerate(hits):
        s = h.fused_score if h.fused_score is not None else 1 / (i + 2)
        tot[h.chunk["doc_id"]] = tot.get(h.chunk["doc_id"], 0.0) + s
    return sorted(tot.items(), key=lambda x: -x[1])


def doc_score_ambiguity(hits: list[Hit], ratio: float = CLARIFY_DOC_RATIO) -> tuple[str, list[str]] | None:
    """En yüksek toplam skorlu doküman ile onunla yer değiştirebilen en iyi doküman: 2. / 1. ≥ ratio ise sorulur.
    En iyi doküman kimseyle yer değiştiremiyorsa (ör. terzilik kitabı) sorulmaz: cevap orada."""
    ranked = doc_scores(hits)
    if not ranked:
        return None
    d1, s1 = ranked[0]
    rivals = [(d, s) for d, s in ranked[1:] if interchangeable(d1, d) and s >= ratio * s1]
    if not rivals:
        return None
    docs = [d1, *[d for d, _ in rivals]]
    return ("products" if BY_ID[d1].doc_type == "product_standard" else "models"), docs


def post_search_ambiguity(hits: list[Hit], min_score: float = CLARIFY_MIN_SCORE, method: str = CLARIFY_METHOD,
                          ratio: float = CLARIFY_DOC_RATIO) -> tuple[str, list[str]] | None:
    """Arama sonrası belirsizlik (R14): ilk 3 sonuç farklı ürün şartnamelerinden ya da aynı ailenin modellerinden geliyorsa
    ('products' | 'models', dokümanlar). Sonuçlar alakasızsa sorulmaz: "Uçak motoru yağı" (Q10) skor −8 ile "hangi model?"
    sorusunu tetikledi. Eşik reranker skoruna bağlı; rerank kapalıyken (varsayılan, skor None) koruma çalışmaz: açık kalan,
    eşik onaylı soru setiyle hibrit/RRF skoruna göre yeniden ayarlanacak (BENCHMARK-RAPORU, bench/clarify_guard.py)."""
    if method == "doc_score":
        relevant = hits[0].rerank_score is None or hits[0].rerank_score >= min_score
        return doc_score_ambiguity(hits, ratio) if relevant else None
    top = list(dict.fromkeys(h.chunk["doc_id"] for h in hits[:3]))
    products = [d for d in top if BY_ID[d].doc_type == "product_standard"]
    relevant = hits[0].rerank_score is None or hits[0].rerank_score >= min_score
    if relevant and len(products) >= 2:
        return "products", products
    return None


def soru_cevapla(question: str, *, brands: list[str] | None = None, doc_ids: list[str] | None = None,
                 mode: str = "hybrid", query_en: str | None = None, on_step=_noop, voice: bool = False,
                 access: list[str] | None = None) -> Result:
    """on_step: arayüzde adım adım durum göstermek için çağrılır ("Kaynaklar aranıyor" ...).
    voice: soru sesle soruldu (STT). Sorudan kaynak çıkmıyorsa arama yapılmadan sorulur (karar).
    access: kullanıcının yetki grupları (None: kontrol yok, pilotun varsayılanı). Arama ve kod eşleşmesi yalnız
    yetkili parçalarda çalışır. Netleştirme seçeneklerindeki doküman adları henüz filtrelenmiyor (BENCHMARK-RAPORU)."""
    timings: dict[str, float] = {}
    t0 = time.time()
    question = spoken_codes(question)     # "Es yetmiş üç yüz A" → "S-7300A": arama ve model yazılı kodu görür
    lang = question_lang(question)
    ctx = analyze_query(question)
    if ctx.foreign_brands:
        # Soruda dokümanı olmayan bir marka geçiyor: başka markanın şartnamesinden değer verilmez (R4).
        # Arama ve model çağrılmaz; cevap saniyeler içinde döner.
        timings["total"] = time.time() - t0
        return _not_found(question, ctx, [], timings,
                          reason=f"Soruda geçen marka için ({', '.join(ctx.foreign_brands)}) sistemde doküman yok.")
    if voice and not doc_ids and not ctx.doc_ids and not brands:
        # Sesli soruda makine, ürün ya da marka geçmiyor: yazılı soruda tüm dokümanlarda aranır, sesli soruda sorulur
        # (karar, cevaplar.md). Usta kısa konuşur ("masura kovanı nasıl takılır?"), yanlış makinenin cevabı riskli.
        timings["total"] = time.time() - t0
        return _clarify(question, ctx, timings, [d.doc_id for d in DOCS],
                        "Sesli soruda makine, ürün ya da marka geçmiyor. Hangi kaynak için?")
    # Soru farklı türden kaynaklara işaret ediyor (makine kılavuzu + ürün şartnamesi: "Brother S-7300A ceket ölçüsü").
    # Seçim yapılmazsa arama ikisinde birden yapılır ve uyum kontrolü (K3) hiç çalışmaz: Kullanıcı denemesinde
    # cevap, S-7300A kılavuzundan "ceket ölçüsü 5 mm veya 7 mm" oldu. Bu yüzden belirsizlik gibi sorulur.
    mixed = len({BY_ID[d].doc_type for d in ctx.doc_ids if BY_ID[d].doc_type in MUST_MATCH}) >= 2
    if (ctx.variants or mixed) and not doc_ids:
        # Belirsiz (ör. "S-7300" → A mı B mi, "US Army" → ceket mi pantolon mu): arama ve model çağrılmadan sorulur.
        # Kullanıcı seçince soru, seçilen dokümanla (doc_ids) yeniden çalıştırılır (cevaplar.md: listeden seçsin).
        # Soruda başka türde bir varlık da varsa (ör. "Brother A ... ceket"), o kaynak da seçenek olur.
        others = [d for d in ctx.doc_ids if d not in ctx.variants]
        products = all(BY_ID[d].doc_type == "product_standard" for d in ctx.variants)
        msg = ("Soru farklı kaynaklara uyuyor (makine kılavuzu ve ürün şartnamesi). Hangisinde arayalım?" if others
               else "Bu markanın birden fazla ürün şartnamesi var. Hangi ürün için?" if products
               else "Soru birden fazla modele uyuyor. Hangi model için?")
        timings["total"] = time.time() - t0
        return _clarify(question, ctx, timings, list(ctx.variants) + others, msg)
    if doc_ids:
        # Kullanıcı kaynak seçti: sorudaki bir varlık bu tür kaynakta eşleşmesi gereken türdense (query.MUST_MATCH)
        # ve seçilen kaynakta karşılığı yoksa model çağrılmaz. Örn. "Brother A makinesi ceket ölçüsü" + S-7300A:
        # kılavuz ürüne özgü bilgi içermez (model alakasız "5 mm" yazmıştı).
        gone = missing_entities(ctx, list(doc_ids))
        if gone:
            where = ", ".join(sorted({BY_ID[d].product for e in gone for d in e[2]}))
            chosen = ", ".join(BY_ID[d].product for d in doc_ids)
            terms = ", ".join(f"'{e[0]}'" for e in gone)
            timings["total"] = time.time() - t0
            result = _not_found(question, ctx, [], timings,
                                reason=f"Seçilen kaynak ({chosen}) sorudaki {terms} için bilgi içermez. "
                                       f"Bu bilgi şu kaynakta olabilir: {where}.",
                                suggest=list(dict.fromkeys(d for e in gone for d in e[2])))
            # Kullanıcı aslında makine ayarını soruyor olabilir ("ceket dikerken iplik gerginliği"): ürün adı
            # çıkarılmış soruyla aynı kaynakta arama seçeneği. Hangisini kastettiğine kullanıcı karar verir.
            bare = strip_terms(question, [e[0] for e in gone if e[1] == "urun"])
            if bare != question and bare.strip():
                result.answer["yalin_soru"] = bare
            return result
    scope = list(doc_ids) if doc_ids else (list(ctx.doc_ids) or None)

    # Seçilen kaynak için bağlam olan varlıklar (ceket şartnamesinde "Brother") aramadan ve modelden çıkarılır:
    # Arama onlara benzeyen parçaları öne almasın, model de "kaynak Brother için değil" diye reddetmesin.
    context = context_entities(ctx, scope) if scope else []
    asked = strip_terms(question, context) if context else question
    # Kod biçimi korpustaki yazıma ("e50" → "E050"): arama ve kod araması aynı kodu görür (query.normalize_codes)
    asked = normalize_codes(asked, scope)

    if scope and asks_nothing_specific(question, ctx):
        # Kaynak belli ama soru neyi sorduğunu söylemiyor ("ceket ölçüsü"): arama rastgele tablolar getirir.
        # Model çağrılmadan sorulur; kullanıcı ayrıntıyı kendisi yazar.
        names = ", ".join(f"{BY_ID[d].brand} · {BY_ID[d].product}" for d in scope)
        timings["total"] = time.time() - t0
        return _clarify(question, ctx, timings, [],
                        f"Soruda hangi bilginin istendiği belli değil (kaynak: {names}). Hangisini arıyorsunuz?",
                        hint="Sorunuza ayrıntı ekleyin.")

    # Atölye terimleri aramada kılavuz terimleriyle genişletilir (R16); kaynak ifadesi ("X kitabına göre") aramadan
    # çıkarılır, kaynak zaten filtrede. Modele giden soru değişmez.
    search_q, added = expand_query(strip_source_phrases(asked, source_aliases(ctx, scope)))
    on_step("Kaynaklar aranıyor" + (f" (terim sözlüğü: {', '.join(added)})" if added else ""))
    t = time.time()
    # doc_score netleştirmesi bütün adaylara bakar (ilk FUSED_K); modele yine ilk TOP_K_SOURCES gider
    wide = CLARIFY_METHOD == "doc_score" and not scope
    c_mode = config.ANSWER_MODE == "c"
    top_k = config.ANSWER_TOP_K if c_mode else TOP_K_SOURCES
    extra_kw: dict[str, Any] = {}
    if c_mode and query_en is None:
        tr = _translator(search_q, scope)
        if tr is not None:
            extra_kw = {"translate": tr, "translate_limit_s": config.TRANSLATE_LIMIT_S}
    candidates = search(search_q, brands=brands, doc_ids=scope, mode=mode,
                        top_k=max(top_k, FUSED_K) if wide else top_k, query_en=query_en, access=access, **extra_kw)
    hits = candidates[:top_k]
    timings["search"] = time.time() - t

    found, missing, elsewhere = code_lookup(asked, scope, brands, access)
    if missing and not found:
        # Sorulan kod kapsamdaki dokümanlarda hiç geçmiyor: benzer bir kodun açıklaması verilmez, model çağrılmaz.
        names = ", ".join(BY_ID[d].product for d in scope) if scope else "dokümanlar"
        other = list(dict.fromkeys(d for c in missing for d in elsewhere.get(c, [])))
        where = f" Bu kod şu kaynakta geçiyor: {', '.join(BY_ID[d].product for d in other)}." if other else ""
        timings["total"] = time.time() - t0
        return _not_found(question, ctx, hits, timings,
                          reason=f"{', '.join(missing)} kodu {names} içinde geçmiyor.{where}", suggest=other)
    if found:
        # Kodun birebir geçtiği parçalar kaynaklarda yoksa başa eklenir (sınır korunur)
        have = {h.chunk["chunk_id"] for h in hits}
        extra = [Hit(c, -1, None) for c in found if c["chunk_id"] not in have]
        hits = (extra + hits)[:top_k]

    if not hits or (MIN_RERANK_SCORE is not None and hits[0].rerank_score is not None
                    and hits[0].rerank_score < MIN_RERANK_SCORE):
        timings["total"] = time.time() - t0
        return _not_found(question, ctx, hits, timings)

    if not doc_ids and not ctx.doc_ids and config.K7_RULE and not _product_in_translation():
        # Arama sonrası belirsizlik (R14): soru kaynak belirtmiyor ve ilk sonuçlar birbirinin yerine geçebilecek
        # dokümanlardan geliyor. Model çağrılmadan sorulur:
        #   - farklı ürün şartnameleri ("Dış görünür dikişlerde SPI?" → ceket 11 (± 1), pantolon 10-14)
        #   - aynı ailenin modelleri ("Masura kovanı nasıl takılır?" → S-7300A ve S-7300B aynı bölüm; model 158 sn
        #     çalışıp "hangi model?" diye sordu, kullanıcı ayrıntı yazınca iki kılavuzdan karışık alıntı yaptı)
        amb = post_search_ambiguity(candidates if CLARIFY_METHOD == "doc_score" else hits)
        if amb:
            kind, docs = amb
            msg = ("Soru birden fazla ürünün şartnamesine uyuyor ve değerler ürüne göre değişebilir. Hangi ürün için?"
                   if kind == "products" else
                   "Bilgi birden fazla modelin kılavuzunda var; ayar ve değerler modele göre değişebilir. "
                   "Hangi model için?")
            timings["total"] = time.time() - t0
            return _clarify(question, ctx, timings, docs, msg, hits)

    on_step("Cevap hazırlanıyor (model)")
    t = time.time()
    # Cevap sorunun dilinde (karar). Dil koddan belirlenir ve açıkça verilir: Talimat yalnızca "soru Türkçe ise
    # Türkçe" diyordu, İngilizce soruya da Türkçe cevap geliyordu (kullanıcı denemesi, test sorusu 20).
    user = f"{format_sources(hits)}\n\n<cevap_dili>{lang.upper()}</cevap_dili>\n\n<soru>\n{asked}\n</soru>"
    if c_mode:
        return _answer_c(question, ctx, hits, user, timings, t0, t, lang, context, added, doc_ids)
    try:
        answer, stats = chat_json(user)
        timings.update({k: float(v) for k, v in stats.items()})
    except json.JSONDecodeError as err:
        # model JSON'u okunamadı: kesik (finish=length) ya da geçersiz; cevap güvenilmez, hat çökmez
        timings["llm"] = time.time() - t
        timings["total"] = time.time() - t0
        broken = {"bulunamadi": False, "alintilar": [], "cevap": "", "sesli_metin": "",
                  "netlestirme_sorusu": None, "celiski_var": False}
        from .jsonparse import failure_message
        bad = Verification("failed", [failure_message(err)], {})
        return Result(question, ctx, hits, broken, bad, "", timings, context_terms=context)
    timings["llm"] = time.time() - t

    sources = {no: h.chunk["text"] for no, h in enumerate(hits, start=1)}
    # Netleştirme seçenekleri (beden, stil ...) yalnız kaynakta geçiyorsa sunulur: seçilince soruya eklenir
    options = clarify_options(answer.get("netlestirme_secenekleri", []), sources)
    answer["netlestirme_secenekleri"] = options
    asks = (answer.get("netlestirme_sorusu") or "").strip()

    if not answer.get("bulunamadi") and not (answer.get("cevap") or "").strip() and asks:
        # Model cevap yazmadan netleştirme istedi: "doğrulanamadı" yerine kullanıcıya sorulur. Kaynak seçilmemişse
        # bulunan dokümanlar düğme olarak sunulur (serbest yazılan "a makinesi" bir modele eşlenemiyor), kaynak
        # belliyse kullanıcı ayrıntı yazar ya da kaynakta geçen seçeneklerden birini seçer.
        timings["total"] = time.time() - t0
        found = [] if (doc_ids or ctx.doc_ids) else list(dict.fromkeys(h.chunk["doc_id"] for h in hits))
        return _clarify(question, ctx, timings, found if len(found) >= 2 else [], asks, hits,
                        aspects=[(o, o) for o in options],
                        hint="Sorunuza ayrıntı ekleyin.", llm_called=True)
    if asks and len(options) < 2:
        # Cevap var ama model kaynakta karşılığı olmayan bir ayrım sordu (SPI sorusunda "hangi beden?"):
        # kullanıcının cevaplayamayacağı soru gösterilmez, denetim için saklanır.
        answer["atlanan_netlestirme"] = asks
        answer["netlestirme_sorusu"] = None
        answer["netlestirme_secenekleri"] = []

    on_step("Kaynakla kontrol ediliyor")
    t = time.time()
    generated = {no: h.chunk.get("generated", "") for no, h in enumerate(hits, start=1)}
    verification = verify(answer, sources, generated)
    timings["verify"] = time.time() - t

    variant = None
    if verification.status in ("verified", "partial") and not (answer.get("netlestirme_sorusu") or "").strip():
        # Değer tablodaki bir varyanta (model, beden ...) özgü ve soru/cevap hangisi olduğunu söylemiyor: seçenekler
        # tablodan sunulur, cevap 'kısmen' olur ve seslendirilmez (yanlış varyantın değeri yanlış değerdir).
        srcs = {no: h.chunk for no, h in enumerate(hits, start=1)}
        sibs = {no: table_siblings(c) for no, c in srcs.items() if c.get("chunk_type") == "table_row"}
        variant = variant_check(answer, question, srcs, sibs)
        if variant:
            answer["netlestirme_sorusu"], answer["netlestirme_secenekleri"] = variant
            verification.status = "partial"
            verification.checks["varyant_belirli"] = False
            verification.problems.append("Değer tablodaki seçeneğe göre değişiyor; cevap hangisi için olduğunu "
                                         "söylemiyor. Aşağıdan seçin.")

    speech = ""
    say = normalize_for_speech if lang == "tr" else normalize_for_speech_en
    if verification.status in ("verified", "partial") and answer.get("sesli_metin") and not variant:
        if (verification.checks.get("sesli_tolerans_tam") is False
                or question_lang(answer["sesli_metin"]) != lang):
            # R15: Model sesli metinde toleransı düşürdü. Ses, doğrulanmış cevaptan kodla üretilir.
            # Aynısı dil için: İngilizce soruda cevap İngilizce, sesli metin Türkçe geldi ("6-10 sütun per inç").
            speech = say(answer.get("cevap") or "")
        else:
            speech = say(answer["sesli_metin"])
    timings["total"] = time.time() - t0
    return Result(question, ctx, hits, answer, verification, speech, timings, expanded_terms=added,
                  context_terms=context, lang=lang)


def _answer_c(question: str, ctx: QueryContext, hits: list[Hit], user: str, timings: dict[str, float], t0: float,
               t: float, lang: str, context: list[str], added: list[str], doc_ids: list[str] | None) -> Result:
    """c kipi: model "tur" seçer (cevap | netlestirme | bulunamadi); öğe başına doğrulama (schema_c.verify_c, alan
    etiketi kuralı dahil). Pipeline'ın serbest metin kuralları (clarify_options, tablo varyant kuralı) bu yolda yok:
    ölçülen hat böyleydi (Adım 2 planı §26). Arayüz için bugünkü biçim (to_legacy) + "ogeler"."""
    from .cloud import ServiceUnavailable
    from .jsonparse import failure_message
    from .schema_c import QUOTE_LIMIT, first_verified_time, item_quotes, to_legacy, verify_c
    timings["istek_oncesi"] = t - t0          # sorudan cevap isteğine (arama ve kurallar dahil)
    try:
        ans, rec = chat_c(user)
    except ServiceUnavailable as err:
        timings["llm"] = time.time() - t
        timings["total"] = time.time() - t0
        down = {"bulunamadi": False, "alintilar": [], "cevap": "", "sesli_metin": "", "netlestirme_sorusu": None,
                "celiski_var": False, "servis_yok": True, "servis_hatasi": str(err)[:300]}
        return Result(question, ctx, hits, down, Verification("failed", [SERVICE_DOWN], {}), "", timings,
                      context_terms=context, lang=lang)
    except json.JSONDecodeError as err:
        timings["llm"] = time.time() - t
        timings["total"] = time.time() - t0
        broken = {"bulunamadi": False, "alintilar": [], "cevap": "", "sesli_metin": "",
                  "netlestirme_sorusu": None, "celiski_var": False}
        return Result(question, ctx, hits, broken, Verification("failed", [failure_message(err)], {}), "", timings,
                      context_terms=context, lang=lang)
    timings["llm"] = time.time() - t
    if rec.get("first_token") is not None:
        timings["llm_first_token"] = float(rec["first_token"])
    sources = {no: h.chunk["text"] for no, h in enumerate(hits, start=1)}
    generated = {no: h.chunk.get("generated", "") for no, h in enumerate(hits, start=1)}
    v = verify_c(ans, sources, generated, QUOTE_LIMIT[config.ANSWER_SCHEMA_VARIANT])
    answer = to_legacy(ans)
    answer.update(sema="c", saglayici=rec.get("provider"), denemeler=rec.get("denemeler"),
                  maliyet=float((rec.get("usage") or {}).get("cost") or 0.0),
                  ham=rec.get("content", ""), akis_zaman=rec.get("zaman") or [])      # denetim ve kayıttan yeniden puanlama
    tur = ans.get("tur")
    if tur == "netlestirme" and v["status"] == "clarify":
        docs = list(dict.fromkeys(hits[n - 1].chunk["doc_id"] for n in v.get("secenekler") or []))
        timings["total"] = time.time() - t0
        msg = ((ans.get("netlestirme") or {}).get("soru") or "Değer ürüne göre değişiyor. Hangisi için?").strip()
        res = _clarify(question, ctx, timings, docs if len(docs) >= 2 and not doc_ids else [], msg, hits,
                       hint="Sorunuza ayrıntı ekleyin.", llm_called=True)
        res.answer.update({k: answer[k] for k in ("sema", "saglayici", "denemeler", "maliyet", "ham", "akis_zaman")})
        return res
    if tur == "bulunamadi" and v["status"] == "not_found":
        timings["total"] = time.time() - t0
        answer["bulunamadi"] = True
        return Result(question, ctx, hits, answer, Verification("not_found", [], {}), "", timings,
                      context_terms=context, lang=lang)
    items = ans.get("cevap") or []
    answer["ogeler"] = [{"metin": x.get("metin", ""), "kaynaklar": [q.get("kaynak_no") for q in item_quotes(x)],
                         "dogrulandi": it["ok"], "sekil": it["sekil"], "sorunlar": it["sorunlar"]}
                        for x, it in zip(items, v["items"])]
    first = first_verified_time(rec.get("content", ""), rec.get("zaman") or [], v["items"]) if v["items"] else None
    if first is not None:
        timings["ilk_dogrulanmis_cumle"] = first
        failed = sum(a.get("sn") or 0.0 for a in (rec.get("denemeler") or [])[:-1])   # yedeğe geçişten önceki denemeler
        timings["uctan_uca_ilk_dogrulanmis"] = timings["istek_oncesi"] + failed + first
    verification = Verification(v["status"] if v["status"] in ("verified", "partial", "failed") else "failed",
                                v["problems"][:6], {"sesli_metin_sayilari": bool(v.get("sesli_ok"))})
    speech = ""
    say = normalize_for_speech if lang == "tr" else normalize_for_speech_en
    if verification.status in ("verified", "partial"):
        voice = ans.get("sesli_metin") or ""
        speech = say(voice if voice and v.get("sesli_ok") and question_lang(voice) == lang
                     else " ".join(x.get("metin", "") for x in items))
    timings["total"] = time.time() - t0
    return Result(question, ctx, hits, answer, verification, speech, timings, expanded_terms=added,
                  context_terms=context, lang=lang)
