"""Sorgu analizi (kural tabanlı): sorudaki varlıklar (makine, ürün, marka) → doküman filtresi,
seçilen kaynakla uyum ve sorunun neyi sorduğunu belirtip belirtmediği. Akış: MIMARI.md §4."""
import json
import re
from dataclasses import dataclass
from functools import lru_cache

from .config import CHUNKS_PATH
from .registry import BRAND_ALIASES, BY_ID, CUSTOMER_BRANDS, DOCS


_TR_LOWER = str.maketrans({"I": "ı", "İ": "i"})


def _squash(text: str) -> str:
    """Karşılaştırma için: küçük harf (Türkçe I/İ), '-', boşluk, '.' ve '_' atılmış."""
    return re.sub(r"[\s\-_.]+", "", text.translate(_TR_LOWER).lower())


# Varlık türü: Sorudaki ifade hangi tür dokümana işaret ediyor.
#   makine: makine modeli / makine markası (kılavuz)    urun: ürün adı (şartname)
#   marka:  müşteri markası (şartnamenin sahibi)          rehber: genel terzilik kaynağı
KIND_OF_DOC_TYPE = {"machine_manual": "makine", "product_standard": "urun", "tailoring_guide": "rehber"}

# Seçilen kaynağın türüne göre sorudaki varlığın rolü (MIMARI.md §4.3):
#   True  → eşleşmeli: Kaynak bu türden bilgiye göre değişir. Varlık seçilen kaynakta yoksa cevap başka bir şey
#           içindir (ör. S-7300A kılavuzunda "ceket" bilgisi olmaz; Nike sorusuna US Army şartnamesi cevap olmaz).
#   False → bağlam: Kaynaktaki bilgi bu varlığa göre değişmez (ceket şartnamesi hangi makinede dikilirse dikilsin aynı).
# Tabloda olmayan kaynak türünde (rehber) hiçbir varlık engellemez.
MUST_MATCH: dict[str, dict[str, bool]] = {
    "machine_manual":   {"makine": True,  "urun": True,  "marka": False},
    "product_standard": {"makine": False, "urun": True,  "marka": True},
}


@dataclass(frozen=True)
class QueryContext:
    doc_ids: tuple[str, ...]      # boşsa filtre yok
    matched: tuple[str, ...]      # hangi ifadeler eşleşti (arayüzde gösterilir)
    foreign_brands: tuple[str, ...] = ()   # soruda geçen ama dokümanı olmayan marka (ör. "Nike")
    variants: tuple[str, ...] = ()         # belirsiz: soru aynı türden birden çok dokümana uyuyor (S-7300 → A, B)
    # Sorudaki her varlık: (eşleşen ifade, tür, doküman kimlikleri).
    # Kullanıcı bir kaynak seçtiğinde, varlığın seçilen kaynakta karşılığı var mı diye bakılır (MUST_MATCH).
    entities: tuple[tuple[str, str, tuple[str, ...]], ...] = ()


# Dokümanı olmayan bilinen markalar. Soruda geçerse model çağrılmadan "bu marka için doküman yok" denir:
# Başka bir markanın şartnamesinden değer vermek yanlış marka hatasıdır (R4). Gerçek sistemde bu liste
# müşteri/marka kaydından gelir ve yetki kontrolüyle birleşir (kullanıcının yetkisi olmayan marka da aynı cevabı alır).
# "Mavi", "Koton", "Gap" gibi aynı zamanda sıradan kelime olan adlar bilinçli olarak dışarıda.
FOREIGN_BRANDS: dict[str, str] = {
    "Nike": r"nike", "Adidas": r"adidas", "Puma": r"puma", "Reebok": r"reebok", "Asics": r"asics",
    "New Balance": r"new\s*balance", "Under Armour": r"under\s*armou?r", "Zara": r"zara", "Mango": r"mango",
    "H&M": r"h\s*&\s*m\b", "LC Waikiki": r"lc\s*waikiki", "DeFacto": r"defacto", "Levi's": r"levi'?s",
    "Tommy Hilfiger": r"tommy\s*hilfiger", "Hugo Boss": r"hugo\s*boss", "Uniqlo": r"uniqlo",
    "Decathlon": r"decathlon", "Columbia": r"columbia", "The North Face": r"north\s*face", "Lacoste": r"lacoste",
    "Ralph Lauren": r"ralph\s*lauren", "Calvin Klein": r"calvin\s*klein", "Primark": r"primark",
    "Bershka": r"bershka", "Pull&Bear": r"pull\s*&\s*bear", "Massimo Dutti": r"massimo\s*dutti",
}


def _foreign_brands(question: str) -> tuple[str, ...]:
    q = question.casefold()
    # Başta kelime sınırı; sonda Türkçe ek gelebilir ("Nike'ın", "Nikelarda")
    return tuple(name for name, pat in FOREIGN_BRANDS.items() if re.search(rf"(?<![\w]){pat}", q))


# --- Söylenmiş kodlar: "Es yetmiş üç yüz A" → "S-7300A", "E sıfır elli" → "E050" ---------------------------
# Sesli soruda Whisper kodu söylendiği gibi yazabiliyor (kullanıcı denemesi, 2026-10-13): "S-7300A" tanınmayınca
# kaynak belirsiz sanılıp "hangi model?" soruluyordu. Yalnızca bir kod harfinden sonra gelen sayı kelimeleri
# çevrilir; "bir sorun", "iki iplik" gibi sıradan metne dokunulmaz.
# "de" bilerek yok: bağlaçtır ("... de iki ..."), D ile başlayan kod pilot dokümanlarında yok.
_LETTERS = {"es": "S", "s": "S", "e": "E", "a": "A", "be": "B", "b": "B", "ce": "C", "c": "C", "d": "D",
            "ka": "K", "ke": "K", "k": "K", "pe": "P", "p": "P", "te": "T", "t": "T", "ha": "H", "he": "H"}
_UNITS_TR = {"bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5, "altı": 6, "yedi": 7, "sekiz": 8, "dokuz": 9}
_TENS_TR = {"on": 10, "yirmi": 20, "otuz": 30, "kırk": 40, "elli": 50, "altmış": 60, "yetmiş": 70, "seksen": 80,
            "doksan": 90}
_NUM_WORDS = set(_UNITS_TR) | set(_TENS_TR) | {"sıfır", "yüz", "bin"}


def _code_digits(words: list[str]) -> str:
    """Kodun sayı kelimeleri → rakam dizisi. Kod rakam rakam da okunabilir: "sıfır elli" → "050", "bir üç üç" → "133".
    Konuşma dilindeki yüzler: "yetmiş üç yüz" → 7300 (yetmiş üç kere yüz)."""
    out, value, last = [], 0, None

    def close():
        nonlocal value, last
        if last is not None:
            out.append(str(value))
        value, last = 0, None

    for w in words:
        if w == "sıfır":
            close()
            out.append("0")
        elif w in _UNITS_TR:
            if last == "unit" or value % 10:
                close()
            value, last = value + _UNITS_TR[w], "unit"
        elif w in _TENS_TR:
            if last in ("unit", "ten") or value % 100:
                close()
            value, last = value + _TENS_TR[w], "ten"
        elif w == "yüz":
            part = value % 1000
            value, last = value - part + (part * 100 if part else 100), "hundred"
        elif w == "bin":
            value, last = (value or 1) * 1000, "thousand"
    close()
    return "".join(out)


def spoken_codes(text: str) -> str:
    """'Es yetmiş üç yüz A'da E sıfır elli hatası' → "S-7300A'da E050 hatası". Kod yoksa metin aynen döner."""
    tokens = text.split(" ")
    out, i = [], 0
    while i < len(tokens):
        letter = _LETTERS.get(tokens[i].translate(_TR_LOWER).lower())
        j = i + 1
        while j < len(tokens) and re.sub(r"['’].*|[.,?!]$", "", tokens[j]).translate(_TR_LOWER).lower() in _NUM_WORDS:
            j += 1
        if letter is None or j == i + 1:
            out.append(tokens[i])
            i += 1
            continue
        words = [re.sub(r"['’].*|[.,?!]$", "", t).translate(_TR_LOWER).lower() for t in tokens[i + 1:j]]
        tail = tokens[j - 1][len(re.sub(r"['’].*|[.,?!]$", "", tokens[j - 1])):]     # son sayının eki: "elli'de"
        digits = _code_digits(words)
        suffix = ""
        if not tail and j < len(tokens):             # model harfi: "... yüz A'da" / "... yüz be"
            m = re.fullmatch(r"([A-Za-z]{1,2})(['’].*|[.,?!])?", tokens[j])
            if m and m.group(1).lower() in ("a", "b", "be"):
                suffix, tail = ("B" if m.group(1).lower() == "be" else m.group(1).upper()), m.group(2) or ""
                j += 1
        sep = "-" if suffix or len(digits) >= 4 else ""
        out.append(f"{letter}{sep}{digits}{suffix}{tail}")
        i = j
    return " ".join(out)


_TR_HINTS = {"ne", "nedir", "nasıl", "kaç", "mı", "mi", "mu", "mü", "için", "olmalı", "hangi", "neden", "ve", "bir",
             "ile", "var", "yok", "değil", "ayarlanır", "takılır", "makinesi", "makinesinde", "hatası", "dikiş"}
_EN_HINTS = {"the", "how", "what", "which", "is", "are", "for", "of", "many", "much", "should", "does", "do", "on",
             "in", "to", "with", "machine", "required", "per", "when", "why", "can"}


def question_lang(question: str) -> str:
    """Sorunun dili: 'tr' ya da 'en'. Cevap sorunun dilinde verilir (karar). Emin olunamazsa Türkçe."""
    if re.search(r"[çğıöşüÇĞİÖŞÜ]", question):
        return "tr"
    words = re.findall(r"[a-z]+", question.lower())
    en, tr = sum(w in _EN_HINTS for w in words), sum(w in _TR_HINTS for w in words)
    return "en" if en > tr else "tr"


def analyze_query(question: str) -> QueryContext:
    q = _squash(spoken_codes(question))
    doc_ids: list[str] = []
    matched: list[str] = []
    entities: list[tuple[str, str, tuple[str, ...]]] = []
    variants: list[str] = []

    for doc in DOCS:
        for alias in doc.aliases:
            if _squash(alias) in q:
                doc_ids.append(doc.doc_id)
                matched.append(alias)
                entities.append((alias, KIND_OF_DOC_TYPE.get(doc.doc_type, "rehber"), (doc.doc_id,)))
                break
    # Model kodu belirtilmemiş makine markası ("Brother") ya da aile kodu ("S-7300"): modellerin hepsi, belirsiz.
    # Müşteri markası ("US Army"), ürün belirtilmemişse: o markanın şartnamelerinin hepsi, belirsiz.
    groups = [(b, "makine", ids) for b, ids in BRAND_ALIASES.items()]
    groups.append(("s7300", "makine", ("brother-s7300a", "brother-s7300b")))
    groups += [(b, "marka", ids) for b, ids in CUSTOMER_BRANDS.items()]
    for alias, kind, ids in groups:
        # "s7300", "S-7300A" eşleşmesinin bir parçasıysa ayrı varlık değildir
        if alias not in q or any(e[2] == ids or alias in _squash(e[0]) for e in entities):
            continue
        entities.append((alias, kind, ids))
        # Daha belirgin bir eşleşme varsa ("Brother S-7300A", "US Army ceket") filtre ona göre kalır,
        # grup yalnızca varlık olarak kaydedilir (kaynak uyumu ve "soru ne soruyor" kontrolü için).
        if not any(i in doc_ids for i in ids):
            doc_ids += list(ids)
            variants += list(ids)
            matched.append(alias)
    return QueryContext(tuple(dict.fromkeys(doc_ids)), tuple(matched), _foreign_brands(question),
                        tuple(dict.fromkeys(variants)), tuple(entities))


def family(doc_id: str) -> set[str]:
    """Aynı makine ailesindeki dokümanlar (S-7300A → {A, B}). Aile yoksa yalnız kendisi."""
    for ids in BRAND_ALIASES.values():
        if doc_id in ids:
            return set(ids)
    return {doc_id}


def _must_match(kind: str, scope: list[str]) -> bool:
    return any(MUST_MATCH.get(BY_ID[d].doc_type, {}).get(kind, False) for d in scope)


def missing_entities(ctx: QueryContext, scope: list[str]) -> list[tuple[str, str, tuple[str, ...]]]:
    """Sorudaki varlıklardan, seçilen kaynak türü için eşleşmesi gerekip (MUST_MATCH) seçilen kaynakta karşılığı
    olmayanlar. Aynı ailedeki modeller birbirinin yerine geçebilir ("diğer modelde ara" engellenmez).

    "Brother A makinesi ceket ölçüsü" + S-7300A → 'ceket' eksik (kılavuz ürüne özgü bilgi içermez).
    Aynı soru + Ceket şartnamesi → 'brother' bağlamdır, eksik sayılmaz (şartname makineden bağımsız).
    """
    reach = set().union(*(family(d) for d in scope)) if scope else set()
    return [e for e in ctx.entities if _must_match(e[1], scope) and not reach & set(e[2])]


def context_entities(ctx: QueryContext, scope: list[str]) -> list[str]:
    """Seçilen kaynak için bağlam olan (aramayı ve cevabı etkilememesi gereken) varlık ifadeleri."""
    reach = set().union(*(family(d) for d in scope)) if scope else set()
    return [e[0] for e in ctx.entities if not _must_match(e[1], scope) and not reach & set(e[2])]


def strip_terms(question: str, aliases: list[str]) -> str:
    """Sorudan verilen ifadelerle başlayan kelimeleri çıkarır ("Brother'da", "ceketin" dahil)."""
    keys = [_squash(a) for a in aliases]
    words = [w for w in question.split() if not any(_squash(w).startswith(k) for k in keys)]
    return " ".join(words)


# --- Soru neyi soruyor? ----------------------------------------------------------------------------
# Kaynak belli olsa bile "ceket ölçüsü" bir şey sormuyor: şartnamede beden tablosu, dikiş sıklığı, punteriz
# ölçüsü ... hepsi "ölçü". Bu durumda arama rastgele tablolar getiriyor, model de uydurmaya ya da boş cevaba
# kayıyor (Windows denemesi, 2026-10-13). Soruda varlıklar ve genel kelimeler dışında hiçbir şey kalmıyorsa
# model çağrılmadan "hangi bilgi?" diye sorulur.

# Tek başına bir şey sormayan kelimeler (kelime başı eşleşir: "ölçüsü", "makinesinde", "dikişleri")
GENERIC_PREFIXES = ("ölçü", "değer", "bilgi", "özellik", "dikiş", "ayar", "makine", "marka", "model", "ürün",
                    "şartname", "kılavuz", "manuel", "detay", "hakkında")
STOPWORDS = {"ne", "nedir", "neler", "nelerdir", "kaç", "kadar", "nasıl", "mı", "mi", "mu", "mü", "mıdır", "midir",
             "için", "icin", "ile", "ve", "veya", "ya", "da", "de", "bir", "bu", "şu", "olmalı", "olmalıdır",
             "olması", "olur", "olan", "var", "yok", "hangi", "hangisi", "gerekir", "gerekli", "lazım", "acaba",
             "the", "of", "for", "what", "is", "are", "an", "in", "on", "how", "much", "many", "which"}


def asks_nothing_specific(question: str, ctx: QueryContext) -> bool:
    """Soruda varlık adları, genel kelimeler ve bağlaçlar dışında kelime yoksa True ("Brother A ceket ölçüsü")."""
    keys = [_squash(e[0]) for e in ctx.entities] + [_squash(b) for b in ctx.foreign_brands]
    for word in re.findall(r"[\w'’\-]+", question.translate(_TR_LOWER).lower()):
        w = _squash(re.split(r"['’]", word)[0])       # "S-7300A'da" → "s7300a"
        if len(w) <= 1 or w in STOPWORDS or w.startswith(GENERIC_PREFIXES) or any(w.startswith(k) for k in keys):
            continue
        return False
    return True


# Soru bir şey sormuyorsa sunulan konular: (düğme etiketi, soruya eklenecek ifade, kaynakta geçiyor mu deseni).
# Yalnızca seçilen kaynakta gerçekten geçen konular sunulur.
ASPECTS: dict[str, tuple[tuple[str, str, str], ...]] = {
    # Dikiş sıklığı dikiş türüne göre değişir (ceket: dış görünür 11 (± 1), overlok 10 (± 2), IFF 8 (± 1)):
    # tek bir "SPI" seçeneği yine belirsiz kalıyordu (gerçek veri denemesi), seçenekler dikiş türüyle verilir.
    "product_standard": (
        ("Dış görünür dikiş SPI", "dış görünür dikişlerde inç başına dikiş (outside visible stitching, stitches per inch)",
         r"outside visible stitching"),
        ("Overlok SPI", "overlok dikişlerinde inç başına dikiş (overedge, stitches per inch)",
         r"overedge[^.]{0,80}stitches per inch"),
        ("İlik dikiş sayısı", "düğme iliklerinde dikiş sayısı (buttonhole stitches)", r"buttonhole"),
        ("Dikiş tipi", "dikiş tipi (stitch type)", r"stitch type|type \d{3}"),
        ("Punteriz ölçüsü", "punteriz ölçüsü (bartack)", r"bar-?tack"),
        ("Dikiş payı", "dikiş payı (seam allowance)", r"seam allowance"),
    ),
    "machine_manual": (
        ("Dikiş hızı", "maksimum dikiş hızı (sewing speed)", r"sewing speed"),
        ("Dikiş uzunluğu", "dikiş uzunluğu (stitch length)", r"stitch length"),
        ("İplik gerginliği", "iplik gerginliği ayarı (thread tension)", r"thread tension"),
        ("Baskı ayağı", "baskı ayağı (presser foot)", r"presser foot"),
        ("İğne", "iğne (needle)", r"\bneedle\b"),
    ),
}
DETAIL_HINT = {
    "product_standard": "Beden tablosundaki bir ölçü için beden ve ölçü noktasını yazın (ör. 'Medium Regular kol boyu').",
    "machine_manual": "Ör. 'E133 hatası', 'yağlama', 'geri dikiş ayarı'.",
}


@lru_cache(maxsize=1)
def _doc_texts() -> dict[str, str]:
    texts: dict[str, list[str]] = {}
    if CHUNKS_PATH.exists():
        with CHUNKS_PATH.open(encoding="utf-8") as f:
            for line in f:
                c = json.loads(line)
                texts.setdefault(c["doc_id"], []).append(c["text"].lower())
    return {d: "\n".join(t) for d, t in texts.items()}


def aspects_for(doc_ids: list[str]) -> list[tuple[str, str]]:
    """Seçilen kaynak(lar)da geçen konular: [(etiket, eklenecek ifade)]. İndeks yoksa hepsi."""
    texts = _doc_texts()
    out: list[tuple[str, str]] = []
    for doc_type in dict.fromkeys(BY_ID[d].doc_type for d in doc_ids):
        for label, phrase, pat in ASPECTS.get(doc_type, ()):
            if not texts or any(re.search(pat, texts.get(d, "")) for d in doc_ids):
                out.append((label, phrase))
    return list(dict.fromkeys(out))
