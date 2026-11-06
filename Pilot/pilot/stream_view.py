"""Gri "doğrulanıyor" akışı (karar 2026-11-06, seçenek C; Adım 2 planı §31). Arayüze henüz bağlı değil.

Metin akarken gri gösterilir; DEĞER taşıyan parçalar doğrulanana kadar gizlidir. Ses ve rozet yalnız doğrulanmış
cümleyle. Gizleme kuralı genel (belgeye özel değil):
  - rakam içeren her parça: değer, aralık (10-14), kesir (1/2), tolerans (±1), birimli değer ("5 mm": birim de),
    hata kodu (E050), model numarası (S-7300A)
  - yazıyla 1–12 (TR/EN; TR'de "on" = 10 da)
Öğe doğrulanınca açılır; ✖ olursa açılmaz, cümle yerine "değer doğrulanamadı, kaynağa bakın" ve kaynak kartı.
Ölçüm: "ilk görünen kelime" = akışta ilk öğenin gizlenmeyen ilk tam kelimesinin geldiği an.
"""
from __future__ import annotations

import re

HIDE = "▒"
_WORDS_EN = "one two three four five six seven eight nine ten eleven twelve".split()
_WORDS_TR = "bir iki üç dört beş altı yedi sekiz dokuz on onbir oniki".split()
# Birimler (genel ölçü birimleri; sayıdan hemen sonra gelirse onunla gizlenir)
UNITS = ("mm cm m km in inch inches inç inc ″ \" ' ft µm um mil g kg mg lb oz n nm kn v kv a ma w kw hz khz rpm "
         "sti/min dk dakika sn saniye s sec min h saat °c °f ° % ‰ bar psi pa kpa mpa l ml cc tex den dtex spi").split()
_UNIT_RE = "|".join(sorted((re.escape(u) for u in UNITS), key=len, reverse=True))
# rakam sayılanlar: \d + daireli/çevrili rakamlar (① ❶ ➀ ➊ ⓵ ⓫ …), kesir karakterleri (½ ⅓), üst simge (² ³ ¹), ±
_DIGITISH = r"\d±①-⓿❶-➓¼-¾⅐-⅟²³¹"
_NUM_TOKEN = re.compile(rf"[^\s]*[{_DIGITISH}][^\s]*(?:\s+(?:{_UNIT_RE})(?![\w]))?", re.I)   # ± tek başına da
_TOKEN = re.compile(r"\S+")


def _word_re(lang: str) -> re.Pattern:
    words = _WORDS_TR if lang == "tr" else _WORDS_EN
    return re.compile(r"(?<!\w)(" + "|".join(words) + r")(?!\w)", re.I)


def hidden_spans(text: str, lang: str = "tr") -> list[tuple[int, int]]:
    """Gizlenecek [başlangıç, bitiş) aralıkları."""
    spans = [m.span() for m in _NUM_TOKEN.finditer(text)]
    spans += [m.span() for m in _word_re(lang).finditer(text)]
    spans.sort()
    out: list[tuple[int, int]] = []
    for s, e in spans:
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def mask(text: str, lang: str = "tr") -> str:
    """Akan (doğrulanmamış) metnin gösterilecek hali: gizlenen parçalar HIDE ile."""
    out, last = [], 0
    for s, e in hidden_spans(text, lang):
        out += [text[last:s], HIDE * 3]
        last = e
    return "".join(out + [text[last:]])


def item_text_spans(content: str) -> list[tuple[int, int]]:
    """Ham JSON akışında "cevap" listesindeki her öğenin "metin" değerinin [başlangıç, bitiş) konumu (değer içi; alıntı
    nesnelerinin "metin"i hariç). Akış yarım olabilir: son değer bitmemişse bitiş = metnin sonu."""
    i = content.find('"cevap"')
    if i < 0:
        return []
    j = content.find("[", i)
    if j < 0:
        return []
    out: list[tuple[int, int]] = []
    stack: list[str] = ["["]
    k, n = j + 1, len(content)
    last_key, expect_value = None, False
    while k < n and stack:
        ch = content[k]
        if ch == '"':
            # dize: sonunu bul
            m = k + 1
            esc = False
            while m < n:
                c = content[m]
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    break
                m += 1
            item_level = len(stack) == 2 and stack[-1] == "{"
            if expect_value:
                if item_level and last_key == "metin":
                    out.append((k + 1, m))
                expect_value = False
            else:
                # anahtar mı? (ardından ':' gelirse)
                rest = content[m + 1:m + 4].lstrip()
                if rest.startswith(":"):
                    last_key = content[k + 1:m]
            k = m + 1
            continue
        if ch == ":":
            expect_value = True
        elif ch in "{[":
            stack.append(ch)
            expect_value = False
        elif ch in "}]":
            stack.pop()
            expect_value = False
        elif ch == ",":
            expect_value = False
        k += 1
    return out


def first_visible_word_offset(content: str, lang: str = "tr") -> int | None:
    """Akışta ilk görünen (gizlenmeyen, tamamlanmış) kelimenin bittiği karakter konumu."""
    for s, e in item_text_spans(content):
        value = content[s:e]
        hidden = hidden_spans(value, lang)
        for m in _TOKEN.finditer(value):
            complete = m.end() < len(value) or e < len(content)    # ardından boşluk/tırnak geldi
            if not complete:
                break
            if not any(hs < m.end() and m.start() < he for hs, he in hidden) and re.search(r"[^\W\d_]", m.group(0)):
                return s + m.end()
    return None


def first_visible_word_time(content: str, timeline: list[list[float]], lang: str = "tr") -> float | None:
    """İlk görünen kelimenin akışta geldiği an (timeline: [[sn, o ana kadarki karakter], ...])."""
    off = first_visible_word_offset(content, lang)
    if off is None:
        return None
    return next((t for t, c in timeline if c >= off), None)


# ---------- Olay üretici: akıştan olaylar (API planı §3–§4, §10; sıra kuralı B) ----------

def item_bounds(content: str) -> list[tuple[int, int]]:
    """"cevap" listesinde KAPANMIŞ her öğenin [başlangıç, bitiş) konumu (öğe nesnesi, süslü parantezler dahil)."""
    i = content.find('"cevap"')
    j = content.find("[", i) if i >= 0 else -1
    if j < 0:
        return []
    out, depth, in_str, esc, start = [], 0, False, False, None
    for k in range(j + 1, len(content)):
        ch = content[k]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = k
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                out.append((start, k + 1))
        elif ch == "]" and depth == 0:
            break
    return out


def _unescape(raw: str) -> str:
    """Akıştaki (yarım olabilen) JSON dizesi parçası → metin. Sonda yarım kaçış dizisi varsa atılır."""
    import json
    for cut in range(0, 7):
        try:
            return json.loads('"' + raw[:len(raw) - cut] + '"')
        except ValueError:
            continue
    return ""


TAMAMLANAMADI = "Cevap tamamlanamadı, kaynağa bakın."
DOGRULANAMADI = "Değer doğrulanamadı, kaynağa bakın."


class StreamAssembler:
    """Model akışından arayüz/servis olayları. feed(birikmiş_içerik, sn) her parçada çağrılır.

    Olaylar (emit(dict)): oge_akis {i, metin (maskeli)}, oge_dogrulandi {i, metin, kaynaklar, sekil},
    oge_dogrulanamadi {i, mesaj, kaynaklar}, oge_sifirla {}, cevap_tamamlanamadi {mesaj}.
    Sıra kuralı B: öğe metinleri gizli sayılarıyla hemen akar; açılış sıralıdır (imleç), ✖ sırayı tıkamaz.
    Doğrulama: schema_c.check_item (alıntı birebir, alan etiketi, sayılar kendi alıntısında, tolerans)."""

    def __init__(self, sources: dict, generated: dict | None, limit: int, lang: str, emit) -> None:
        self.sources, self.generated, self.limit, self.lang, self.emit = sources, generated or {}, limit, lang, emit
        self.reset_state()
        self.ilk_gorunen_kelime: float | None = None
        self.ilk_dogrulanmis: float | None = None

    def reset_state(self) -> None:
        self.shown: dict[int, str] = {}       # öğe → gönderilen maskeli metin
        self.checked: list[dict] = []         # kapanan öğelerin doğrulama sonucu (sırayla)
        self.cursor = 0                       # açılış imleci
        self.verified_sent = 0

    def feed(self, content: str, t: float) -> None:
        from .schema_c import check_item
        spans = item_text_spans(content)
        bounds = item_bounds(content)
        for i, (s, e) in enumerate(spans):
            if i < self.cursor:                      # açılmış öğeye gri metin bir daha gitmez
                continue
            closed = i < len(bounds)
            text = _unescape(content[s:e])
            if not closed and e >= len(content) and " " in text:
                text = text[:text.rfind(" ")]           # yarım kelime gönderilmez (rakam taşıyabilir)
            elif not closed and e >= len(content):
                text = ""
            masked = mask(text, self.lang)
            if masked and masked != self.shown.get(i):
                self.shown[i] = masked
                self.emit({"olay": "oge_akis", "i": i, "metin": masked})
                if self.ilk_gorunen_kelime is None and re.search(r"[^\W\d_]{2,}", masked):
                    self.ilk_gorunen_kelime = t
        import json
        while len(self.checked) < len(bounds):
            s, e = bounds[len(self.checked)]
            try:
                item = json.loads(content[s:e], strict=False)
            except ValueError:
                item = {}
            r = check_item(item, self.sources, self.generated, self.limit) if item else {"ok": False, "kaynaklar": [], "sekil": False}
            self.checked.append({"item": item, **r})
        self._reveal(t)

    def _reveal(self, t: float) -> None:
        while self.cursor < len(self.checked):
            i, r = self.cursor, self.checked[self.cursor]
            nos = [n for n in (r.get("kaynaklar") or []) if isinstance(n, int)]
            if r["ok"]:
                self.emit({"olay": "oge_dogrulandi", "i": i, "metin": r["item"].get("metin", ""), "kaynaklar": nos,
                           "sekil": r.get("sekil", False)})
                self.verified_sent += 1
                if self.ilk_dogrulanmis is None:
                    self.ilk_dogrulanmis = t
            else:
                self.emit({"olay": "oge_dogrulanamadi", "i": i, "mesaj": DOGRULANAMADI, "kaynaklar": nos})
            self.cursor += 1

    def retry_allowed(self) -> bool:
        """Akış ortası kesintide yeniden deneme yalnız henüz doğrulanmış öğe gönderilmediyse (API planı §4)."""
        return self.verified_sent == 0

    def reset(self) -> None:
        """Yedeğe geçiş: akan gri metin silinir (doğrulanmış öğe yokken)."""
        self.reset_state()
        self.emit({"olay": "oge_sifirla"})

    def interrupted(self) -> None:
        """Doğrulanmış öğe gönderildikten sonra kesinti: kalan için mesaj."""
        self.emit({"olay": "cevap_tamamlanamadi", "mesaj": TAMAMLANAMADI})
