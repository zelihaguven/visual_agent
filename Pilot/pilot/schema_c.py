"""Cevap şeması C (Adım 2 planı §15.0, karar 2026-11-05; uygulamaya bağlama §29, 2026-11-06).

Çalışma biçimi c150b-J (config.ANSWER_SCHEMA_VARIANT). bench.schema_c bu modülün kendisidir (ölçüm araçları aynı kodu
kullanır).

Üst düzey "tur": cevap | netlestirme | bulunamadi (model birini seçer; aynı anda hem sorup hem cevap yazamaz).
    cevap        [{alinti: {kaynak_no, metin}, metin}]: her cümle kendi alıntısını hemen önünde taşır; metinde [n] yok,
                 liste numarası dizi sırasından.
    netlestirme  {soru, secenekler: [{kaynak_no}] (en az 2)}: seçenekler kaynak numarası; arayüz belge/ürün adını
                 kendisi gösterir (clarify_options süzgecine gerek yok).
    bulunamadi   cevap boş.
Doğrulama öğe başına: alıntı kaynakta birebir; cümlenin sayıları YALNIZ kendi alıntısında; tolerans; sesli metnin
sayıları bütün alıntıların birleşiminde. Akışta her öğe tamamlanınca doğrulanabilir: "ilk doğrulanmış cümle" zamanı.
"""
import json
import re
from typing import Any

from . import verify as V
from .prompts import SYSTEM_PROMPT

ANSWER_SCHEMA_C: dict[str, Any] = {
    "type": "object",
    "required": ["tur", "cevap", "sesli_metin", "celiski_var"],
    "properties": {
        "tur": {"type": "string", "enum": ["cevap", "netlestirme", "bulunamadi"]},
        "netlestirme": {"type": "object", "required": ["soru", "secenekler"], "properties": {
            "soru": {"type": "string", "maxLength": 150},
            "secenekler": {"type": "array", "minItems": 2, "maxItems": 6, "items": {
                "type": "object", "required": ["kaynak_no"], "properties": {"kaynak_no": {"type": "integer"}}}}}},
        "cevap": {"type": "array", "maxItems": 8, "items": {
            "type": "object", "required": ["alinti", "metin"], "properties": {
                "alinti": {"type": "object", "required": ["kaynak_no", "metin"], "properties": {
                    "kaynak_no": {"type": "integer"}, "metin": {"type": "string", "maxLength": 300}}},
                "metin": {"type": "string", "maxLength": 250}}}},
        "sesli_metin": {"type": "string", "maxLength": 250},
        "celiski_var": {"type": "boolean"},
    },
}

# Uygulamanın talimatı; yalnız alanlara ve biçime ilişkin kurallar C'ye uyarlanır (içerik kuralları aynı).
_REPLACE = [
    ('   - Kaynaklarda soruya cevap yoksa "bulunamadi" alanını true yap, "cevap" ve "sesli_metin" alanlarını boş bırak.',
     '   - Kaynaklarda soruya cevap yoksa "tur" alanını "bulunamadi" yap; "cevap" listesini ve "sesli_metin"i boş bırak.'),
    ("""   - Cevaba dayanak olan her cümleyi, kaynaktaki dilinde ve KELİMESİ KELİMESİNE "alintilar" alanına yaz. \\
Alıntıyı çevirme, kısaltma, düzeltme. Her alıntının hangi kaynak numarasından geldiğini belirt.
   - Her alıntı 1-2 cümle olsun. Uzun bir prosedürü tek alıntıya kopyalama: en önemli cümleleri ayrı kısa \\
alıntılar olarak ver, adımları "cevap" alanında kendi cümlelerinle sırala.
   - "cevap" alanını boş bırakma: Cevap bulunduysa adımları veya değeri "cevap" alanına yaz.""",
     """   - "cevap" bir listedir; her öğe bir cümle ya da bir adımdır. Her öğede ÖNCE "alinti": o cümlenin dayandığı \\
kaynak cümlesi, kaynaktaki dilinde ve KELİMESİ KELİMESİNE (1-2 cümle; çevirme, kısaltma, düzeltme) ve kaynak numarası; \\
SONRA "metin": cümlenin kendisi.
   - Her cümle kendi alıntısına dayanmalı: Cümledeki her sayı ve kod o öğenin alıntısında geçmeli.
   - Adımları ayrı öğeler olarak sırala; adım numarası yazma, sıra öğe sırasıdır."""),
    ("SADECE alıntılardan, yazıldığı gibi aktar.", "SADECE o cümlenin kendi alıntısından, yazıldığı gibi aktar."),
    ("   - Cevaptaki her bilgi cümlesinin sonuna kaynak numarasını [1] biçiminde yaz. Sayfa numarası yazma.",
     '   - Cümle metnine kaynak numarası ya da [1] yazma: Atıf, öğenin alıntısındaki "kaynak_no"dur.'),
    ("""   - Soruda ürün belli değilse ve kaynaklar farklı ürünler için farklı değer veriyorsa "netlestirme_sorusu" alanına \\
kısa bir soru yaz ve değerleri ürün adıyla birlikte ver.
   - Kaynaktaki değer bir ayrıntıya göre değişiyorsa (beden, stil, model, kullanım türü) ve soruda bu ayrıntı yoksa \\
"netlestirme_sorusu" alanına kısa bir soru, "netlestirme_secenekleri" alanına kullanıcının seçebileceği değerleri \\
KAYNAKTA YAZDIĞI GİBİ yaz (ör. "X-Small", "Medium"). Değer böyle bir ayrıntıya göre değişmiyorsa netleştirme sorma, \\
"netlestirme_secenekleri" alanını boş bırak.""",
     """   - Soruda ürün/model belli değilse ve kaynaklar farklı ürünler için FARKLI değer veriyorsa "tur" alanını \\
"netlestirme" yap: "netlestirme.soru" alanına kısa bir soru, "netlestirme.secenekler" alanına seçilebilecek her ürünün \\
kaynak numarasını yaz (en az 2). Bu durumda "cevap" listesini boş bırak.
   - Değer ürünlerde AYNIYSA netleştirme sorma: "tur" = "cevap", her ürünün kaynağından alıntıyla cevap ver.
   - Aynı anda hem netleştirme sorup hem cevap yazma."""),
    ("   - Cevap kısa ve doğrudan olsun: önce cevabın özü, sonra gerekiyorsa numaralı adımlar. Güvenlik uyarılarını atlama.",
     "   - Cevap kısa ve doğrudan olsun: ilk öğe cevabın özü, sonra gerekiyorsa adımlar ayrı öğeler. Güvenlik uyarılarını atlama."),
    ('   - "sesli_metin" alanına cevabın 1-3 cümlelik kısa halini',
     '   - "sesli_metin" alanına cevabın 1-3 cümlelik kısa halini (yalnız alıntılardaki sayılarla)'),
]


def system_prompt_c() -> str:
    p = SYSTEM_PROMPT
    for old, new in _REPLACE:
        old, new = old.replace("\\\n", ""), new.replace("\\\n", "")    # kaynak dosyadaki satır birleştirme gibi
        if old not in p:
            raise ValueError(f"istem parçası bulunamadı (uygulama istemi değişmiş): {old[:60]!r}")
        p = p.replace(old, new)
    return p


# Süre ölçümü varyantları (karar 2026-11-05 gece; bütün modellerde aynı genel değişiklik):
#   c150   alıntı en fazla 150 karakter, ilk öğe yalnız cevabın özü
#   c150b  c150 + öğe başına 1–2 alıntı ("alintilar", en fazla 2); öğenin sayıları alıntılarının birleşiminde aranır
#   c150bT c150b + tablo hücresi kuralı (karar 2026-11-06, devir d/4): hücreden alıntıda sütun başlığı eklenmez
#   c150bJ c150b + "JSON'u girintisiz, tek satırda yaz" (karar 2026-11-06, plan §24; sağlayıcı girintisi)
#   c150bJM c150bJ + öğede ÖNCE "metin", SONRA "alintilar" (karar 2026-11-06, gri akış C: metin hemen akar)
#   c150bJS c150bJ, "sesli_metin" alanı yok: ses doğrulanmış öğelerden (karar 2026-11-06, API planı §1; JUKI J10)
#   c150bJSN c150bJS + niteleyici kuralı (plan §23 adım 2; B012): sorudaki ayırt edici niteleyici kaynakta yoksa bulunamadı
#   c150bJSNE c150bJSN + niteleyici eşleştirmesi (plan §34): etiket kaynaktır, eşdeğer yazım eşleşir, yer/görünüm
#            sözcüğü niteleyici değil
VARIANTS = ("c", "c150", "c150b", "c150bT", "c150bJ", "c150bJM", "c150bJS", "c150bJSN", "c150bJSNE")
_C150_RULES = [
    ("(1-2 cümle; çevirme, kısaltma, düzeltme)",
     "(en fazla 150 karakter: cümlenin dayandığı en kısa kaynak parçası; çevirme, kısaltma, düzeltme)"),
    ("   - Cevap kısa ve doğrudan olsun: ilk öğe cevabın özü, sonra gerekiyorsa adımlar ayrı öğeler.",
     "   - Cevap kısa ve doğrudan olsun: İLK ÖĞE YALNIZ CEVABIN ÖZÜ (değer ya da tek kısa cümle), sonra gerekiyorsa "
     "adımlar ayrı öğeler."),
]
_C150B_RULES = [
    ('Her öğede ÖNCE "alinti": o cümlenin dayandığı kaynak cümlesi',
     'Her öğede ÖNCE "alintilar": o cümlenin dayandığı 1-2 kaynak parçası (her biri kendi kaynak numarasıyla)'),
    ("ve kaynak numarası; SONRA", "; SONRA"),
    ("Cümledeki her sayı ve kod o öğenin alıntısında geçmeli.", "Cümledeki her sayı ve kod o öğenin alıntılarında geçmeli."),
]


_TABLE_RULE = [
    ("   - Adımları ayrı öğeler olarak sırala; adım numarası yazma, sıra öğe sırasıdır.",
     "   - Adımları ayrı öğeler olarak sırala; adım numarası yazma, sıra öğe sırasıdır.\n"
     "   - Tablo hücresinden alıntıda sütun başlığını ya da başka hücreleri ekleme; hücre metnini olduğu gibi kopyala. "
     "Başlık gerekiyorsa onu ikinci alıntı olarak ver."),
]


_ONE_LINE_RULE = [
    ("Yalnızca istenen JSON şemasına uyan tek bir JSON nesnesi döndür.",
     "Yalnızca istenen JSON şemasına uyan tek bir JSON nesnesi döndür. JSON'u girintisiz, tek satırda yaz: "
     "satır sonu ve hizalama boşluğu kullanma."),
]


_NO_VOICE_RULES = [
    ('"cevap" listesini ve "sesli_metin"i boş bırak.', '"cevap" listesini boş bırak.'),
    ('"cevap" ve "sesli_metin" alanlarını <cevap_dili> etiketindeki dilde yaz',
     '"cevap" alanını <cevap_dili> etiketindeki dilde yaz'),
    ('\n9. Sesli metin\n   - "sesli_metin" alanına cevabın 1-3 cümlelik kısa halini (yalnız alıntılardaki sayılarla) '
     '(cevapla aynı dilde) yaz. Kaynak numarası, parantez, madde işareti kullanma. Sayıları RAKAMLA yaz. Uzun parça '
     'numaralarını koyma.', ''),
]


def schema_variant(name: str) -> tuple[dict[str, Any], str]:
    """(şema, sistem talimatı) varyanta göre; uygulama istemi değişmişse hata verir."""
    import copy
    schema, prompt = copy.deepcopy(ANSWER_SCHEMA_C), system_prompt_c()
    if name == "c":
        return schema, prompt
    item = schema["properties"]["cevap"]["items"]
    item["properties"]["alinti"]["properties"]["metin"]["maxLength"] = 150
    rules = list(_C150_RULES)
    if name in ("c150b", "c150bT", "c150bJ", "c150bJM", "c150bJS", "c150bJSN", "c150bJSNE"):
        quote = item["properties"].pop("alinti")
        item["properties"] = {"alintilar": {"type": "array", "minItems": 1, "maxItems": 2, "items": quote},
                              "metin": item["properties"]["metin"]}
        item["required"] = ["alintilar", "metin"]
        rules += _C150B_RULES + (_TABLE_RULE if name == "c150bT" else []) + (_ONE_LINE_RULE if name in ("c150bJ", "c150bJM", "c150bJS", "c150bJSN", "c150bJSNE") else [])
        if name == "c150bJM":                 # özellik sırası: önce cümle, sonra alıntılar (akışta metin önce gelir)
            item["properties"] = {"metin": item["properties"]["metin"], "alintilar": item["properties"]["alintilar"]}
            item["required"] = ["metin", "alintilar"]
    for old, new in rules:
        if old not in prompt:
            raise ValueError(f"istem parçası bulunamadı: {old[:60]!r}")
        prompt = prompt.replace(old, new)
    if name in ("c150bJS", "c150bJSN", "c150bJSNE"):
        schema["properties"].pop("sesli_metin")
        schema["required"] = [r for r in schema["required"] if r != "sesli_metin"]
        for old, new in _NO_VOICE_RULES:
            if old not in prompt:
                raise ValueError(f"istem parçası bulunamadı: {old[:60]!r}")
            prompt = prompt.replace(old, new)
    if name in ("c150bJSN", "c150bJSNE"):
        old = '   - Kaynaklarda soruya cevap yoksa "tur" alanını "bulunamadi" yap; "cevap" listesini boş bırak.'
        if old not in prompt:
            raise ValueError("istem parçası bulunamadı: niteleyici kuralı")
        rule = ("\n   - Sorudaki ayırt edici niteleyici (ör. dijital, elektronik, -5, Premier, Type II, model kodu) kaynakta "
                "yoksa o konuyu başka bir parçanın bilgisiyle cevaplama; \"tur\" alanını \"bulunamadi\" yap.")
        if name == "c150bJSNE":
            rule += ("\n   - Niteleyici eşleştirmesi: kaynak etiketindeki doküman, marka, ürün ve bölüm adı da kaynaktır. "
                     "Niteleyicinin kaynakta açıkça yazan eşdeğeri de eşleşir: tekil/çoğul ya da birleşik yazım (Type II ↔ "
                     "Types II and III), ayırıcı ya da OCR farkı (-3 ↔ -[][]3), başka dildeki karşılığı (iğne plakası ↔ "
                     "needle plate). Benzer ama farklı bir özellik eşdeğer değildir (dijital ↔ elle/mekanik ayar). Yer, "
                     "görünüm ya da konu sözcükleri (üst, sol taraf, iç yüz) niteleyici değildir.")
        prompt = prompt.replace(old, old + rule)
    if name == "c150bJM":
        m = re.search(r'Her öğede ÖNCE "alintilar": (.*?) ?; SONRA "metin": cümlenin kendisi\.', prompt)
        if not m or "2. Önce alıntı" not in prompt:
            raise ValueError("istem parçası bulunamadı: öğe sırası")
        prompt = prompt.replace(m.group(0), f'Her öğede ÖNCE "metin": cümlenin kendisi; SONRA "alintilar": {m.group(1)}.')
        prompt = prompt.replace("2. Önce alıntı", "2. Cümle ve alıntı")
    return schema, prompt


def item_quotes(item: dict) -> list[dict]:
    """Öğenin alıntıları: "alintilar" (c150b) ya da tek "alinti"."""
    if isinstance(item.get("alintilar"), list):
        return [q for q in item["alintilar"] if isinstance(q, dict)]
    return [item["alinti"]] if isinstance(item.get("alinti"), dict) else []


THOUGHT = re.compile(r"^\s*(?:<think>.*?</think>|<thought>.*?</thought>|<\|?channel\|?>[^{]*?<\|?channel\|?>|"
                     r"<\|?channel\|?>thought[^{]*)\s*", re.S)


def parse_c(content: str, finish: str | None) -> tuple[dict[str, Any] | None, str]:
    """(cevap, json durumu): ok | bos | kesik | gecersiz | sema_disi."""
    text = THOUGHT.sub("", content or "", count=1).strip()
    if not text:
        return None, "bos"
    from . import jsonparse
    m = re.search(r"\{.*\}", text, re.S)
    try:
        ans = jsonparse.loads(m.group(0) if m else text, finish)   # strict=False: kaçışsız sekme vb. (2026-11-06)
    except json.JSONDecodeError:
        # gerçek neden (2026-11-06): finish=length ise kesik, değilse okunamadı
        return None, "kesik" if finish == "length" else "gecersiz"
    ok = (isinstance(ans, dict) and ans.get("tur") in ("cevap", "netlestirme", "bulunamadi")
          and isinstance(ans.get("cevap", []), list)
          and all(isinstance(x, dict) and item_quotes(x) and isinstance(x.get("metin"), str)
                  for x in ans.get("cevap") or []))
    if ok and ans["tur"] == "netlestirme":
        n = ans.get("netlestirme") or {}
        ok = isinstance(n.get("secenekler"), list) and len(n["secenekler"]) >= 2 and not ans.get("cevap")
    return (ans, "ok") if ok else (ans if isinstance(ans, dict) else None, "sema_disi")


# Varyantın alıntı uzunluk sınırı: sınıra dayanıp kesilen alıntıya verify._cut_quote_prefix ile aynı tolerans
# (16 Ekim kuralı; sınır şemadan gelir). 2026-11-05: c150'de sınır 300 sanıldığı için kesik alıntılar ✖ oluyordu.
QUOTE_LIMIT = {"c": 300, "c150": 150, "c150b": 150, "c150bT": 150, "c150bJ": 150, "c150bJM": 150, "c150bJS": 150, "c150bJSN": 150, "c150bJSNE": 150}


def _quote_ok(text: str, no: Any, sources: dict[int, str], limit: int = 300) -> bool:
    if no not in sources:
        return False
    t, s = V.normalize(V.CUT_CITE_RE.sub("", text)), V.normalize(sources[no])
    if t in s:
        return True
    from .tables import field_quote_ok
    if field_quote_ok(V.CUT_CITE_RE.sub("", text), sources[no]):    # "<Sütun>: <hücre parçası>" (2026-11-06)
        return True
    old = V.QUOTE_MAX
    V.QUOTE_MAX = limit
    try:
        return bool(V._cut_quote_prefix(text, s))
    finally:
        V.QUOTE_MAX = old


def ocr_uncertain_in(quote: str, tokens: list[str] | None) -> list[str]:
    """Alıntıda geçen "OCR değeri belirsiz" diziler (iki okuma uyuşmadı; PLAN-OCR §10–§11)."""
    if not tokens:
        return []
    q = V.normalize(quote)
    return [t for t in tokens if V.normalize(t) and V.normalize(t) in q]


def check_item(item: dict, sources: dict[int, str], generated: dict[int, str] | None = None,
               limit: int = 300, uncertain: dict[int, list[str]] | None = None) -> dict[str, Any]:
    """Bir öğe: alıntı birebir, sayılar yalnız kendi alıntısında, tolerans, şekil açıklamasından mı, alıntıda OCR
    değeri belirsiz dizi var mı (uncertain: kaynak no → belirsiz diziler)."""
    qs = item_quotes(item)
    nos = [q.get("kaynak_no") for q in qs]
    no, text = (nos[0] if nos else None), item.get("metin") or ""
    quote = " ".join(q.get("metin") or "" for q in qs)
    problems = []
    bad = [q.get("kaynak_no") for q in qs if not _quote_ok(q.get("metin") or "", q.get("kaynak_no"), sources, limit)]
    exact = bool(qs) and not bad
    for b in bad:
        problems.append(f"alıntı [{b}] kaynakta birebir değil")
    ocr_bad = [t for q in qs for t in ocr_uncertain_in(q.get("metin") or "", (uncertain or {}).get(q.get("kaynak_no")))]
    if ocr_bad:
        problems.append(f"OCR değeri belirsiz: {ocr_bad}")
    stray = sorted(V.numbers_in(text) - V.numbers_in(quote) - V.word_numbers(quote))
    if stray:
        problems.append(f"cümlede kendi alıntısında olmayan sayı: {stray}")
    tol = True
    for m in V.TOL_RE.finditer(quote):
        n, t = V._canon_num(m.group(1)), V._canon_num(m.group(2))
        flat = re.sub(r"\s+", "", text).replace(",", ".").lower()
        if n in V.numbers_in(text) and f"±{t}" not in flat and f"artıeksi{t}" not in flat:
            tol = False
            problems.append(f"tolerans düşmüş: {m.group(0)}")
    figure = any(generated and q.get("kaynak_no") in generated and generated[q.get("kaynak_no")]
                 and V.normalize(q.get("metin") or "") in V.normalize(generated[q.get("kaynak_no")]) for q in qs)
    foreign = bool(V.FOREIGN_SCRIPT_RE.search(text))
    if foreign:
        problems.append("cümlede başka alfabeden karakter")
    ok = exact and not stray and tol and bool(text.strip()) and not foreign and not ocr_bad
    return {"ok": ok, "sekil": figure, "sorunlar": problems, "kaynak_no": no, "kaynaklar": nos,
            "ocr_belirsiz": ocr_bad}


def verify_c(ans: dict, sources: dict[int, str], generated: dict[int, str] | None = None,
             limit: int = 300, uncertain: dict[int, list[str]] | None = None) -> dict[str, Any]:
    """Durum: verified | partial | failed | not_found | clarify; öğe sonuçları ve sesli metin kontrolü."""
    tur = ans.get("tur")
    if tur == "bulunamadi":
        ok = not ans.get("cevap")
        return {"status": "not_found" if ok else "failed", "items": [], "problems": [] if ok else ["bulunamadı ama cevap dolu"]}
    if tur == "netlestirme":
        nos = [o.get("kaynak_no") for o in (ans.get("netlestirme") or {}).get("secenekler") or [] if isinstance(o, dict)]
        valid = [n for n in dict.fromkeys(nos) if n in sources]
        ok = len(valid) >= 2 and not ans.get("cevap")
        return {"status": "clarify" if ok else "failed", "items": [], "secenekler": valid,
                "problems": [] if ok else ["netleştirme seçenekleri geçersiz ya da cevapla birlikte"]}
    items = [check_item(x, sources, generated, limit, uncertain) for x in ans.get("cevap") or []]
    problems = [p for it in items for p in it["sorunlar"]]
    quotes = " ".join(q.get("metin") or "" for x in ans.get("cevap") or [] for q in item_quotes(x))
    voice = ans.get("sesli_metin") or ""
    voice_stray = sorted(V.numbers_in(voice) - V.numbers_in(quotes) - V.word_numbers(quotes))
    if voice_stray:
        problems.append(f"sesli metinde alıntılarda olmayan sayı: {voice_stray}")
    texts = [V.normalize(x.get("metin") or "") for x in ans.get("cevap") or []]
    repeat = len([t for t in texts if len(t.split()) >= 4]) != len({t for t in texts if len(t.split()) >= 4})
    if repeat:
        problems.append("aynı cümle tekrar ediyor")
    if not items:
        status = "failed"
        problems.append("tur=cevap ama cevap listesi boş")
    elif all(i["ok"] for i in items) and not voice_stray and not repeat:
        status = "partial" if any(i["sekil"] for i in items) else "verified"
    else:
        status = "failed"
    return {"status": status, "items": items, "problems": problems, "sesli_ok": not voice_stray}


def item_end_offsets(content: str) -> list[int]:
    """Ham JSON metninde "cevap" listesindeki her öğenin bittiği karakter konumu (akışta o anda doğrulanabilir)."""
    i = content.find('"cevap"')
    if i < 0:
        return []
    j = content.find("[", i)
    out, depth, in_str, esc = [], 0, False, False
    for k in range(j + 1, len(content)):
        ch = content[k]
        if in_str:
            esc = (not esc) and ch == "\\"
            if ch == '"' and not esc:
                in_str = False
            continue
        if ch == '"':
            in_str, esc = True, False
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                out.append(k + 1)
        elif ch == "]" and depth == 0:
            break
    return out


def first_verified_time(content: str, timeline: list[list[float]], items: list[dict]) -> float | None:
    """İlk doğrulanmış öğenin akışta tamamlandığı an (timeline: [[sn, o ana kadarki karakter sayısı], ...]).
    Öğe sırası korunur: ilk öğe geçmezse kullanıcı onu görmez, sonraki geçen öğe gösterilir (zaman onun sonu)."""
    ends = item_end_offsets(content)
    for end, it in zip(ends, items):
        if it["ok"]:
            return next((t for t, n in timeline if n >= end), None)
    return None


def to_legacy(ans: dict) -> dict[str, Any]:
    """Pipeline'ın akışı bozulmasın diye C cevabının bugünkü biçimdeki karşılığı (ölçümde karar C'den verilir)."""
    tur = ans.get("tur")
    items = ans.get("cevap") or []
    return {"alintilar": [q for x in items for q in item_quotes(x)],
            "cevap": " ".join(x.get("metin", "") + "".join(f" [{q.get('kaynak_no')}]" for q in item_quotes(x))
                              for x in items),
            "sesli_metin": ans.get("sesli_metin") or "", "celiski_var": bool(ans.get("celiski_var")),
            "netlestirme_sorusu": (ans.get("netlestirme") or {}).get("soru") if tur == "netlestirme" else None,
            "netlestirme_secenekleri": [], "bulunamadi": tur == "bulunamadi"}


def items_markdown(items: list[dict]) -> str:
    """Arayüz için öğe listesi (§15.1 gösterim): tek öğe paragraf, birden çok öğe numaralı liste (numara koddan),
    her öğenin sonunda kaynak etiketleri [n] koddan; doğrulanamayan öğe işaretli."""
    lines = []
    for i, it in enumerate(items, 1):
        tags = "".join(f"[{n}]" for n in dict.fromkeys(it.get("kaynaklar") or []) if isinstance(n, int))
        mark = "" if it.get("dogrulandi") else " ⚠ *(doğrulanamadı)*"
        text = f"{(it.get('metin') or '').strip()} {tags}{mark}".strip()
        lines.append(text if len(items) == 1 else f"{i}. {text}")
    return "\n".join(lines)
