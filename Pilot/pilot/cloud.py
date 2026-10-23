"""OpenRouter ortak kuralları (rerank, Aşama 4'te embedding). Ürün kararı: ZDR zorunlu.

- Her istek yalnız veri saklamayan (ZDR) ve veriyi toplamayan sağlayıcılara gider: provider = {zdr: true,
  data_collection: deny}. Kapatılamaz; çağıranın gövdedeki provider alanı bunu ezemez. OpenRouter filtreye uymayan
  sağlayıcıya geri düşmez (istek 404 döner).
- ZDR'siz modeller çağrılmaz: istemci kurulurken modelin ZDR uyumlu uç noktası olup olmadığı /endpoints/zdr listesinden
  kontrol edilir; yoksa hiç istek gönderilmeden hata verilir.
- Buluta yalnız sorgu metni ve seçilmiş parçalar gider. Kullanıcı kimliği, yetki bilgisi, ses, doküman tamamı gönderilmez.
- Anahtar yalnız OPENROUTER_API_KEY ortam değişkeninden okunur, hiçbir yere yazılmaz.
"""
import os
from collections.abc import Callable
from functools import lru_cache
from typing import Any

from .config import OPENROUTER_URL

ZDR_PROVIDER = {"zdr": True, "data_collection": "deny"}


def openrouter_body(body: dict[str, Any]) -> dict[str, Any]:
    """İstek gövdesi + zorunlu sağlayıcı kısıtı. Gövdede provider varsa kısıt yine uygulanır (diğer alanları korunur)."""
    provider = {**(body.get("provider") or {}), **ZDR_PROVIDER}
    return {**body, "provider": provider}


def api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY ortam değişkeni tanımlı değil")
    return key


def _fetch_zdr_endpoints() -> list[dict[str, Any]]:
    import requests
    r = requests.get(f"{OPENROUTER_URL}/endpoints/zdr", headers={"Authorization": f"Bearer {api_key()}"}, timeout=30)
    r.raise_for_status()
    return r.json().get("data", [])


@lru_cache(maxsize=1)
def zdr_model_ids() -> frozenset[str]:
    """ZDR uyumlu uç noktası olan modeller (süreç başına bir kez, ücretsiz uç)."""
    return frozenset(e.get("model_id") for e in _fetch_zdr_endpoints() if e.get("model_id"))


def require_zdr(model: str, ids: Callable[[], frozenset[str]] = zdr_model_ids) -> None:
    if model not in ids():
        raise ValueError(f"{model}: ZDR uyumlu sağlayıcısı yok; ZDR zorunlu olduğu için kullanılamaz ve ölçülmez")
