"""Uçtan uca hat: soru_cevapla(). Arayüzden bağımsızdır (Streamlit, test betiği, değerlendirme aynısını çağırır)."""
import json
import time
from dataclasses import dataclass, field
from typing import Any

from .config import CLARIFY_MIN_SCORE, MIN_RERANK_SCORE, TOP_K_SOURCES
from .llm import chat_json
from .query import (DETAIL_HINT, MUST_MATCH, QueryContext, analyze_query, asks_nothing_specific, aspects_for,
                    context_entities, family, missing_entities, question_lang, spoken_codes, strip_terms)
from .registry import BY_ID, DOCS
from .retrieve import Hit, search
from .speech import normalize_for_speech, normalize_for_speech_en
from .terms import expand_query
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
        parts.append(f'<kaynak no="{no}" doküman="{c["doc_id"]}" marka="{c["brand"]}" ürün="{c["product"]}" '
                     f'dil="{LANG_NAMES.get(c["lang"], c["lang"])}" tür="{c["doc_type"]}" bölüm="{section}">\n'
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


def soru_cevapla(question: str, *, brands: list[str] | None = None, doc_ids: list[str] | None = None,
                 mode: str = "hybrid", query_en: str | None = None, on_step=_noop, voice: bool = False) -> Result:
    """on_step: arayüzde adım adım durum göstermek için çağrılır ("Kaynaklar aranıyor" ...).
    voice: soru sesle soruldu (STT). Sorudan kaynak çıkmıyorsa arama yapılmadan sorulur (karar)."""
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

    if scope and asks_nothing_specific(question, ctx):
        # Kaynak belli ama soru neyi sorduğunu söylemiyor ("ceket ölçüsü"): arama rastgele tablolar getirir.
        # Model çağrılmadan, seçilen kaynakta gerçekten geçen konular sunulur.
        names = ", ".join(f"{BY_ID[d].brand} · {BY_ID[d].product}" for d in scope)
        timings["total"] = time.time() - t0
        return _clarify(question, ctx, timings, [],
                        f"Soruda hangi bilginin istendiği belli değil (kaynak: {names}). Hangisini arıyorsunuz?",
                        aspects=aspects_for(scope), hint=DETAIL_HINT.get(BY_ID[scope[0]].doc_type, ""))

    # Atölye terimleri aramada kılavuz terimleriyle genişletilir (R16). Modele giden soru değişmez.
    search_q, added = expand_query(asked)
    on_step("Kaynaklar aranıyor" + (f" (terim sözlüğü: {', '.join(added)})" if added else ""))
    t = time.time()
    hits = search(search_q, brands=brands, doc_ids=scope, mode=mode, top_k=TOP_K_SOURCES, query_en=query_en)
    timings["search"] = time.time() - t

    if not hits or (MIN_RERANK_SCORE is not None and hits[0].rerank_score is not None
                    and hits[0].rerank_score < MIN_RERANK_SCORE):
        timings["total"] = time.time() - t0
        return _not_found(question, ctx, hits, timings)

    if not doc_ids and not ctx.doc_ids:
        # Arama sonrası belirsizlik (R14): soru kaynak belirtmiyor ve ilk sonuçlar birbirinin yerine geçebilecek
        # dokümanlardan geliyor. Model çağrılmadan sorulur:
        #   - farklı ürün şartnameleri ("Dış görünür dikişlerde SPI?" → ceket 11 (± 1), pantolon 10-14)
        #   - aynı ailenin modelleri ("Masura kovanı nasıl takılır?" → S-7300A ve S-7300B aynı bölüm; model 158 sn
        #     çalışıp "hangi model?" diye sordu, kullanıcı ayrıntı yazınca iki kılavuzdan karışık alıntı yaptı)
        top = list(dict.fromkeys(h.chunk["doc_id"] for h in hits[:3]))
        products = [d for d in top if BY_ID[d].doc_type == "product_standard"]
        models = next((ms for ms in ([d for d in top if d in family(x)] for x in top) if len(ms) >= 2), [])
        # Sonuçlar alakasızsa sorulmaz: "Uçak motoru yağı" (Q10) skor −8 ile "hangi model?" sorusunu tetikledi.
        # Eşik kaba: "bulunamadı" eşiği konamadı (skorlar iç içe), ama bu yalnız netleştirmeyi atlar; model yine çalışır.
        relevant = hits[0].rerank_score is None or hits[0].rerank_score >= CLARIFY_MIN_SCORE
        if relevant and (len(products) >= 2 or models):
            msg = ("Soru birden fazla ürünün şartnamesine uyuyor ve değerler ürüne göre değişebilir. Hangi ürün için?"
                   if len(products) >= 2 else
                   "Bilgi birden fazla modelin kılavuzunda var; ayar ve değerler modele göre değişebilir. "
                   "Hangi model için?")
            timings["total"] = time.time() - t0
            return _clarify(question, ctx, timings, products if len(products) >= 2 else models, msg, hits)

    on_step("Cevap hazırlanıyor (model)")
    t = time.time()
    # Cevap sorunun dilinde (karar). Dil koddan belirlenir ve açıkça verilir: Talimat yalnızca "soru Türkçe ise
    # Türkçe" diyordu, İngilizce soruya da Türkçe cevap geliyordu (kullanıcı denemesi, test sorusu 20).
    user = f"{format_sources(hits)}\n\n<cevap_dili>{lang.upper()}</cevap_dili>\n\n<soru>\n{asked}\n</soru>"
    try:
        answer, stats = chat_json(user)
        timings.update({k: float(v) for k, v in stats.items()})
    except json.JSONDecodeError:
        # model JSON'u yarıda bıraktı (token sınırı): cevap güvenilmez, hat çökmez
        timings["llm"] = time.time() - t
        timings["total"] = time.time() - t0
        broken = {"bulunamadi": False, "alintilar": [], "cevap": "", "sesli_metin": "",
                  "netlestirme_sorusu": None, "celiski_var": False}
        bad = Verification("failed", ["Model güvenilir bir cevap üretemedi: çıktı uzunluk sınırında yarıda kesildi "
                                      "(JSON tamamlanmadı). Kaynaklarda bu sorunun cevabı olmayabilir; aşağıdaki "
                                      "kaynak sayfaları kontrol edin, değer kullanmayın."], {})
        return Result(question, ctx, hits, broken, bad, "", timings, context_terms=context)
    timings["llm"] = time.time() - t

    if (not answer.get("bulunamadi") and not (answer.get("cevap") or "").strip()
            and (answer.get("netlestirme_sorusu") or "").strip()):
        # Model cevap yazmadan netleştirme istedi: "doğrulanamadı" yerine kullanıcıya sorulur. Kaynak seçilmemişse
        # bulunan dokümanlar düğme olarak sunulur (serbest yazılan "a makinesi" bir modele eşlenemiyor), kaynak
        # belliyse kullanıcı ayrıntı yazar.
        timings["total"] = time.time() - t0
        found = [] if (doc_ids or ctx.doc_ids) else list(dict.fromkeys(h.chunk["doc_id"] for h in hits))
        kind = BY_ID[hits[0].chunk["doc_id"]].doc_type
        return _clarify(question, ctx, timings, found if len(found) >= 2 else [], answer["netlestirme_sorusu"].strip(),
                        hits, hint=DETAIL_HINT.get(kind, "Sorunuza ayrıntı ekleyin."), llm_called=True)

    on_step("Kaynakla kontrol ediliyor")
    t = time.time()
    sources = {no: h.chunk["text"] for no, h in enumerate(hits, start=1)}
    verification = verify(answer, sources)
    timings["verify"] = time.time() - t

    speech = ""
    say = normalize_for_speech if lang == "tr" else normalize_for_speech_en
    if verification.status in ("verified", "partial") and answer.get("sesli_metin"):
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
