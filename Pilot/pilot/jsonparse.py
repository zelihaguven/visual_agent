"""Model çıktısındaki JSON'un ortak ayrıştırma adımı (bütün modeller ve sağlayıcılar; karar 2026-11-06).

- strict=False: alıntı içindeki kaçışsız sekme gibi kontrol karakterleri kabul edilir. Genel bir sağlamlık ayarıdır,
  modele özel yama değildir (A066: kaynak tablo hücresindeki sekme alıntıya kaçışsız kopyalanmıştı).
- Hata sınıfı gerçek nedeni söyler: sağlayıcı finish=length dediyse "kesik", değilse "JSON okunamadı" + hata türü.
"""
from __future__ import annotations

import json
from typing import Any

DECODER = json.JSONDecoder(strict=False)


class ModelJSONError(json.JSONDecodeError):
    """Model çıktısı JSON olarak okunamadı. truncated: çıktı uzunluk sınırında kesildi (finish=length)."""

    def __init__(self, truncated: bool, detail: str, doc: str = "", pos: int = 0) -> None:
        super().__init__(detail, doc, pos)
        self.truncated, self.detail = truncated, detail


def loads(text: str, finish: str | None = None) -> Any:
    """json.loads(strict=False); hata ModelJSONError (kesik ya da okunamadı)."""
    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError as e:
        raise ModelJSONError(finish == "length", f"{e.msg} (konum {e.pos})", e.doc, e.pos) from e


def raw_decode(text: str) -> tuple[Any, int]:
    """Metnin başındaki JSON nesnesi, kontrol karakteri toleransıyla."""
    return DECODER.raw_decode(text)


def error_detail(text: str) -> str:
    """Okunamayan çıktının hata türü (ör. 'Expecting ',' delimiter (konum 812)'); okunuyorsa boş."""
    try:
        json.loads(text, strict=False)
        return ""
    except json.JSONDecodeError as e:
        return f"{e.msg} (konum {e.pos})"


def failure_message(err: BaseException) -> str:
    """Kullanıcıya gösterilen sorun metni: gerçek neden (kesik / okunamadı)."""
    tail = ("Kaynaklarda bu sorunun cevabı olmayabilir; aşağıdaki kaynak sayfaları kontrol edin, değer kullanmayın.")
    if getattr(err, "truncated", False):
        return ("Model güvenilir bir cevap üretemedi: çıktı uzunluk sınırında yarıda kesildi (JSON tamamlanmadı). "
                + tail)
    detail = getattr(err, "detail", "") or str(err)
    return f"Model güvenilir bir cevap üretemedi: JSON okunamadı ({detail}). " + tail
