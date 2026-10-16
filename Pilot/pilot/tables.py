"""Tablo satırı metni ve varyant kontrolü (kural tabanlı, dokümandan bağımsız).

Tablo satırı parçası şu biçimde: "Satır etiketi | Başlık: değer | Başlık: değer". Birden çok sütunu kaplayan (birleşik)
hücrenin başlığı SPAN_SEP ile birleşir: "MO-6804(D)/DD & MO-6814S(D)/DD: 28 kg" (değer bu sütunların ortak değeri).

Varyant kontrolü: Cevaptaki değer bir tablo boyutuna (model, beden, tip ...) göre değişiyor ve ne soru ne cevap o
boyutun adını söylüyorsa, model bir varyantın değerini genel cevap gibi vermiş olabilir. Seçenekler tablonun kendisinden
gelir; doküman kaydı veya elle yazılmış kural gerekmez.
  - Sütun varyantı: aynı satırda başlıklara göre farklı değerler (JUKI s.3 "Overedge width | MO-6804: 1.5, 4.0 mm |
    MO-6814S: 3.0, 4.0 mm | MO-6816S: 4.0, 5.0, 6.0 mm"; 2026-10-16 J3: cevap yalnız MO-6816S değerlerini "MO-6800S
    için" diye verdi).
  - Satır varyantı: aynı tablonun her satırı bir varyant (JUKI s.36 model seçim tablosu: her alt modelin hızı farklı;
    J4: cevap tek bir alt modelin satırından geldi).
"""
import re
from typing import Any

from .verify import normalize, numbers_in

SPAN_SEP = " & "
MAX_OPTIONS = 6


def segments(text: str) -> tuple[str, list[tuple[list[str], str]]]:
    """Satır etiketi ve (başlıklar, değer) listesi. Başlıksız ilk parça satır etiketidir."""
    label, segs = "", []
    for i, part in enumerate(p.strip() for p in text.split(" | ")):
        head, sep, value = part.partition(": ")
        if not sep or len(head) > 80:
            if i == 0:
                label = part
            continue
        segs.append(([h.strip() for h in head.split(SPAN_SEP)], value.strip()))
    return label, segs


def _core(name: str) -> str:
    """Başlığın karşılaştırma çekirdeği: 'MO-6804(D)/DD' -> 'mo6804', 'Style A' -> 'stylea'."""
    head = re.split(r"[(/]", name, maxsplit=1)[0]
    core = re.sub(r"[^\w]", "", head.casefold())
    return core if len(core) >= 3 else re.sub(r"[^\w]", "", name.casefold())


def _mentions(text: str, names: list[str]) -> bool:
    flat = re.sub(r"[^\w]", "", text.casefold())
    return any((c := _core(n)) and len(c) >= 3 and c in flat for n in names)


def _distinct(values: list[str]) -> bool:
    return len({normalize(v) for v in values}) >= 2


def column_variant(text: str) -> tuple[str, list[str]] | None:
    """Satırın değerleri sütun başlığına göre değişiyorsa (satır etiketi, başlıklar)."""
    label, segs = segments(text)
    # Yalnız matris tablo (başlıksız satır etiketi + varyant sütunları). Kayıt satırında ("Error code: E01 |
    # Description: ...") sütunlar farklı alanlardır, varyant değil.
    single = [(h[0], v) for h, v in segs if len(h) == 1 and v not in ("-", "")]
    heads = [h for h, _ in single]
    # Seçenek olacak başlıklar ad olmalı: sayı/kod başlıklar ("3: For mediumweight") ve tekrar eden başlıklar
    # ("Setting value" x2) kullanıcıya sorulacak bir boyut değil.
    named = all(len(re.findall(r"[A-Za-z]", h)) >= 2 for h in heads) and len(set(heads)) == len(heads)
    # Varyant sütunları paralel: değerler aynı türden ("1.5, 4.0 mm" / "3.0, 4.0 mm"). Öznitelik sütunlarında
    # türler farklı (Brother: "Setting value: 1 - 19 stitches | Setting units: 1 stitch | Initial value: 1").
    parallel = len({frozenset(re.findall(r"[a-z]{2,}", v.casefold())) for _, v in single}) == 1
    if not label or len(single) < 2 or not named or not parallel or not _distinct([v for _, v in single]):
        return None
    return label, heads


def _covers_all(text: str, ans_nums: set[str]) -> bool:
    """Cevap satırdaki bütün sütunların değerlerini veriyor mu (ör. Min ve Max birlikte: aralık, varyant değil)."""
    vals = [numbers_in(v) for h, v in segments(text)[1] if len(h) == 1 and numbers_in(v)]
    return bool(vals) and all(v <= ans_nums for v in vals)


def record_keys(text: str) -> tuple[str, ...] | None:
    """Kayıt biçimli satırın sütunları (aynı tablonun satırlarını bulmak için)."""
    rec = _record(text)
    return tuple(rec) if rec else None


def _record(text: str) -> dict[str, str] | None:
    """Kayıt biçimli satır (her hücrenin başlığı var, birleşik hücre yok): {başlık: değer}. Değilse None.
    Matris tablolarda (JUKI s.3: 'Sewing speed | MO-6804: ...') satır etiketi başlıksızdır: satır varyantı aranmaz."""
    label, segs = segments(text)
    if label or not segs or any(len(h) != 1 for h, _ in segs):
        return None
    return {h[0]: v for h, v in segs}


def row_identifier(rows: list[str], value_head: str) -> tuple[str, list[str]] | None:
    """Kayıt biçimli tablonun satırları bir varyant boyutu mu: (ayırıcı sütun, değerleri) ya da None.
    Ayırıcı sütun: her satırda farklı ve harf içeren ilk sütun (ör. 'Model name'; sıra numarası 'No.' değil).
    value_head: cevaptaki değerin geldiği sütun. Her satırda sayı içermeli ve satırdan satıra değişmeli: hata kodu
    tablosunda açıklamaların çoğu sayı içermez, orada 'hangi kod için?' sorulmaz."""
    recs = [_record(r) for r in rows]
    if len(recs) < 2 or any(r is None for r in recs) or len({tuple(r) for r in recs}) != 1:
        return None
    values = [r.get(value_head, "") for r in recs]
    if not all(numbers_in(v) for v in values) or not _distinct(values):
        return None
    for head in recs[0]:
        if head == value_head:
            continue
        vals = [r[head] for r in recs]
        if len(set(vals)) == len(vals) and all(re.search(r"[A-Za-z]", v) for v in vals):
            return head, vals
    return None


def variant_check(answer: dict[str, Any], question: str, sources: dict[int, dict[str, Any]],
                  siblings: dict[int, list[str]] | None = None) -> tuple[str, list[str]] | None:
    """Cevabın dayandığı tablo satırı bir varyanta özgüyse (mesaj, seçenekler); değilse None.
    sources: {kaynak_no: parça}; siblings: {kaynak_no: aynı tablonun tüm satır metinleri}."""
    said = f"{question} {answer.get('cevap', '')}"
    ans_nums = numbers_in(answer.get("cevap", ""))
    if not ans_nums:
        return None
    for no in dict.fromkeys(q.get("kaynak_no") for q in answer.get("alintilar") or []):
        src = sources.get(no)
        if not src or src.get("chunk_type") != "table_row" or not (numbers_in(src["text"]) & ans_nums):
            continue
        col = column_variant(src["text"])
        if col and not _mentions(said, col[1]) and not _covers_all(src["text"], ans_nums):
            label, heads = col
            what = f" ({label})" if label else ""
            return (f"Bu değer tabloda sütuna göre değişiyor{what}. Hangisi için?", heads[:MAX_OPTIONS])
        own = _record(src["text"])
        rows = (siblings or {}).get(no) or []
        if not own or len(rows) < 2:
            continue
        value_head = next((h for h, v in own.items() if numbers_in(v) & ans_nums), None)
        ident = row_identifier(rows, value_head) if value_head else None
        if ident and not _mentions(said, [own.get(ident[0], "")]):
            head, vals = ident
            return (f"Bu değer tabloda satıra göre değişiyor ({head}). Hangisi için?", vals[:MAX_OPTIONS])
    return None
