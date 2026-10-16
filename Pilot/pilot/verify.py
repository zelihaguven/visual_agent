"""Cevap sonrası otomatik doğrulama (kod tarafı, LLM değil).

Kontroller: kaynak numaraları geçerli mi, alıntı kaynakta birebir geçiyor mu, [n] atıfları,
cevap/sesli metindeki sayılar alıntılarda var mı, kaynaktaki 'N (± t)' toleransı cevapta tam mı,
alıntı şeklin otomatik (VLM) açıklamasından mı geliyor.
"""
import re
from dataclasses import dataclass, field

NUM = r"\d+(?:[.,]\d+)?"
NUM_RE = re.compile(NUM)
TOL_RE = re.compile(rf"({NUM})\s*\(\s*±\s*({NUM})\s*\)")
CITE_RE = re.compile(r"\[(\d+)\]")
# Şema alıntıyı 300 karakterde kesiyor: Model sona atıf yazmaya başlamışsa "... to the right, [" kalıyor
# (masura kovanı sorusu: ilk 299 karakter kaynakla birebir aynıydı). Yarım atıf alıntıdan ayıklanır.
CUT_CITE_RE = re.compile(r"\s*\[\d*$")
# Çince/Japonca/Korece, Kiril, Arap, Yunan (± ve ° gibi işaretler dahil değil). "・" (U+30FB, U+FF65) hariç:
# Brother kılavuzları madde işareti olarak kullanıyor, model alıntıdan cevaba taşıyabilir.
FOREIGN_SCRIPT_RE = re.compile(r"[぀-ヺー-ヿ㐀-鿿가-힯＀-､ｦ-￯"
                               r"Ѐ-ӿ؀-ۿͰ-Ͽ]")
# Harf önekli kodlar (S-7300A, E-07, D6193): içindeki rakamlar bir "değer" değildir.
CODE_RE = re.compile(r"\b[A-Za-z]{1,5}-?\d+[A-Za-z]*\b")


def normalize(text: str) -> str:
    """Boşluk, tırnak ve tire farklarını yok say (karşılaştırma için)."""
    t = text.casefold().replace(" ", " ")
    t = t.replace("’", "'").replace("“", '"').replace("”", '"').replace("–", "-").replace("—", "-")
    t = re.sub(r"\s*-\s*", "-", t)
    return re.sub(r"\s+", " ", t).strip()


def _canon_num(s: str) -> str:
    return s.replace(",", ".")


# Satır başındaki liste numarası ("4. İplik gerginliğini ölçün"): Talimat numaralı adım istiyor, bunlar değer değil
# (iplik gerginliği sorusunda "alıntıda olmayan sayı: 4, 6" yanlış alarmı).
# Satır içi de olabilir: "...izleyin: 1) Güçten ayrıl. 2) Makine başını..." (değerlendirme Q14, Q06). Satır içinde
# yalnız cümle sonu ya da iki noktadan sonra gelip büyük harfle devam eden numara sayılır ("Hız 4. kademe" sayılmaz).
LIST_MARK_RE = re.compile(r"(?:^\s*|(?<=[.:;])\s+)\d{1,2}[.)]\s+(?=[A-ZÇĞİÖŞÜ])|^\s*\d{1,2}[.)]\s+", re.MULTILINE)


def numbers_in(text: str) -> set[str]:
    cleaned = CODE_RE.sub(" ", CITE_RE.sub("", LIST_MARK_RE.sub("", text)))
    return {_canon_num(m.group(0)) for m in NUM_RE.finditer(cleaned)}


def clarify_options(options: list, sources: dict[int, str]) -> list[str]:
    """Modelin netleştirme seçeneklerinden kaynak metinde kelime olarak geçenler (sırası korunur, tekrarsız).
    2026-10-16 denemesi: Model SPI sorusunda "Hangi boy ceket için? Medium, Large, XX-Large?" diye sordu. Kaynakta
    geçmeyen bir ayrım sorulmasın; tek harf ("A") her metinde geçtiği için 2 karakterden kısa seçenek alınmaz."""
    text = " ".join(normalize(s) for s in sources.values())
    kept: list[str] = []
    for o in options or []:
        if not isinstance(o, str):
            continue
        opt = o.strip()
        n = normalize(opt)
        if len(n) >= 2 and opt not in kept and re.search(rf"(?<!\w){re.escape(n)}(?!\w)", text):
            kept.append(opt)
    return kept


@dataclass
class Verification:
    status: str                       # "verified" | "partial" | "not_found" | "failed" | "clarify"
    problems: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)

    @property
    def badge(self) -> str:
        return {"verified": "✔ Doğrulandı", "partial": "⚠ Kısmen doğrulandı",
                "not_found": "✖ Kaynaklarda bulunamadı", "failed": "✖ Doğrulanamadı",
                "clarify": "❓ Netleştirme gerekli"}[self.status]


QUOTE_MAX = 300           # prompts.ANSWER_SCHEMA alıntı uzunluk sınırı
CUT_MARGIN = 15           # sınıra bu kadar yakın alıntı "kesilmiş" sayılır
CUT_MAX_TAIL = 20         # kesilmiş alıntının sonunda kaynakta olmayan en fazla bu kadar karakter olabilir


def _cut_quote_prefix(text: str, norm_source: str) -> str:
    """Uzunluk sınırında kesilen alıntının kaynakla birebir örtüşen başı; değilse boş.
    2026-10-16 (rank patch sorusu): Model 300 karakterlik sınıra dayanan alıntının sonunu bozdu ("(see figure 1)"
    yerine "(see **[1"): ilk ~290 karakter birebir olduğu halde cevap "doğrulanamadı" oldu ve seslendirilmedi.
    Yalnız sınıra dayanan alıntıda ve kısa bir kuyrukta uygulanır: kısa alıntıdaki fark hâlâ hatadır."""
    n = normalize(text)
    if len(text) < QUOTE_MAX - CUT_MARGIN:
        return ""
    words = n.split(" ")
    for k in range(len(words) - 1, 0, -1):
        head = " ".join(words[:k])
        if head in norm_source:
            return head if len(n) - len(head) <= CUT_MAX_TAIL else ""
    return ""


def verify(answer: dict, sources: dict[int, str], generated: dict[int, str] | None = None) -> Verification:
    """answer: LLM'in JSON çıktısı. sources: {kaynak_no: chunk metni}.
    generated: {kaynak_no: metnin model üretimi kısmı} (şekil açıklaması). Oradan yapılan alıntı birebir olsa da
    kaynak metni değildir: cevap en fazla "kısmen doğrulandı" olur."""
    if answer.get("bulunamadi"):
        ok = not answer.get("cevap", "").strip()
        return Verification("not_found" if ok else "failed",
                            [] if ok else ["bulunamadi=true ama cevap dolu"], {"bos_cevap": ok})
    problems: list[str] = []
    checks: dict[str, bool] = {}

    quotes = answer.get("alintilar") or []
    checks["alinti_var"] = bool(quotes)
    if not quotes:
        problems.append("Cevap var ama alıntı yok")

    norm_sources = {no: normalize(t) for no, t in sources.items()}
    norm_generated = {no: normalize(t) for no, t in (generated or {}).items() if t}
    exact, from_figure = True, False
    for q in quotes:
        # Model alıntının sonuna atıf ekleyebiliyor ("... 4000 sti/min [1]"). Atıf kaynağın parçası değil,
        # karşılaştırmadan önce ayıklanır; alıntının kendisi yine birebir olmalı.
        no, text = q.get("kaynak_no"), CUT_CITE_RE.sub("", CITE_RE.sub("", q.get("metin", ""))).strip()
        if no not in norm_sources:
            problems.append(f"Geçersiz kaynak numarası: {no}")
            exact = False
        elif normalize(text) not in norm_sources[no]:
            kept = _cut_quote_prefix(text, norm_sources[no])
            if kept:
                problems.append(f"Alıntı [{no}] uzunluk sınırında kesildi; kaynakla örtüşen ilk {len(kept)} karakter "
                                "kullanıldı")
            else:
                problems.append(f"Alıntı kaynakta birebir bulunamadı: {text[:70]!r}")
                exact = False
        elif no in norm_generated and normalize(text) in norm_generated[no]:
            from_figure = True
            problems.append(f"Alıntı [{no}] şeklin otomatik açıklamasından (model üretimi, kaynak metni değil): "
                            "şekli kaynak sayfada kontrol edin")
    checks["alinti_birebir"] = exact
    checks["alinti_kaynak_metni"] = not from_figure

    cites = {int(c) for c in CITE_RE.findall(answer.get("cevap", ""))}
    cites_ok = bool(cites) and cites <= set(sources)
    checks["atif_gecerli"] = cites_ok
    if not cites_ok:
        problems.append("Cevapta geçerli [n] atfı yok" if not cites else f"Geçersiz atıf: {sorted(cites - set(sources))}")

    quote_text = " ".join(q.get("metin", "") for q in quotes)
    quote_nums = numbers_in(quote_text)
    text_ans = answer.get("cevap", "")
    text_voice = answer.get("sesli_metin", "")
    stray = sorted((numbers_in(text_ans) | numbers_in(text_voice)) - quote_nums)
    checks["sayilar_alintida"] = not stray
    if stray:
        problems.append(f"Alıntıda olmayan sayı(lar): {stray}")

    # Tolerans cevapta ve sesli metinde AYRI AYRI kontrol edilir (R15: ekranda "11 (± 1)", seste "on bir").
    def _has_tol(text: str, t: str) -> bool:
        flat = re.sub(r"\s+", "", text).replace(",", ".").lower()
        return f"±{t}" in flat or f"artıeksi{t}" in flat or f"plusorminus{t}" in flat

    tol_ok, voice_tol_ok = True, True
    for m in TOL_RE.finditer(quote_text):
        n, t = _canon_num(m.group(1)), _canon_num(m.group(2))
        if n in numbers_in(text_ans) and not _has_tol(text_ans, t):
            tol_ok = False
            problems.append(f"Tolerans düşmüş: kaynak '{m.group(0)}', cevapta ± {t} yok")
        if n in numbers_in(text_voice) and not _has_tol(text_voice, t):
            voice_tol_ok = False
            problems.append(f"Sesli metinde tolerans düşmüş: kaynak '{m.group(0)}', seste ± {t} yok "
                            "(sesli metin doğrulanmış cevaptan yeniden üretilir)")
    checks["tolerans_tam"] = tol_ok
    checks["sesli_tolerans_tam"] = voice_tol_ok   # sert hata değil: pipeline sesi cevaptan üretir

    checks["cevap_var"] = bool(text_ans.strip())
    if not checks["cevap_var"]:
        problems.append("Model 'bulunamadı' demeden boş cevap döndürdü")

    # Tekrar döngüsü: Küçük model aynı cümleyi defalarca yazabiliyor (masura kovanı sorusu, 2026-10-13: alıntı doğru,
    # cevap "Dili wraps ettirdiğiniz bir masura tutarak..." x4). Sayı içermediği için diğer kontrollerden geçiyordu.
    sentences = [normalize(CITE_RE.sub("", s)) for s in re.split(r"[.!?]+", text_ans)]
    sentences = [s for s in sentences if len(s.split()) >= 4]
    checks["tekrar_yok"] = len(sentences) == len(set(sentences))
    if not checks["tekrar_yok"]:
        problems.append("Cevapta aynı cümle tekrar ediyor: model döngüye girdi, cevap güvenilmez")

    # Yabancı alfabe: qwen modelleri üretim sırasında Çinceye kayabiliyor (kullanıcı denemesi, iplik gerginliği
    # sorusu: cevap tamamen Çince, alıntının sonuna "金额不足" eklenmiş). Kaynaklar ve cevap Latin alfabesinde.
    foreign = FOREIGN_SCRIPT_RE.findall(f"{text_ans} {text_voice}")
    checks["alfabe_dogru"] = not foreign
    if foreign:
        problems.append(f"Model cevaba başka dilde metin karıştırdı ({''.join(foreign[:6])}...): cevap güvenilmez")

    hard = not (checks["alinti_var"] and checks["alinti_birebir"] and checks["sayilar_alintida"]
                and checks["tolerans_tam"] and checks["cevap_var"] and checks["tekrar_yok"] and checks["alfabe_dogru"])
    problems = list(dict.fromkeys(problems))   # model aynı alıntıyı tekrarlayabiliyor: uyarı bir kez gösterilir
    if hard:
        return Verification("failed", problems, checks)
    return Verification("verified" if cites_ok and not from_figure else "partial", problems, checks)
