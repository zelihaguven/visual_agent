"""OpenRouter ortak kuralları (rerank, Aşama 4'te embedding). Ürün kararı: ZDR zorunlu.

- Her istek yalnız veri saklamayan (ZDR) ve veriyi toplamayan sağlayıcılara gider: provider = {zdr: true,
  data_collection: deny}. Kapatılamaz; çağıranın gövdedeki provider alanı bunu ezemez. OpenRouter filtreye uymayan
  sağlayıcıya geri düşmez (istek 404 döner).
- ZDR'siz modeller çağrılmaz: istemci kurulurken modelin ZDR uyumlu uç noktası olup olmadığı /endpoints/zdr listesinden
  kontrol edilir; yoksa hiç istek gönderilmeden hata verilir.
- Saklama sınıfı uç nokta düzeyinde: /endpoints/zdr listesi "Safety Retention" uç noktalarını da içeriyor (güvenlik
  incelemesi için istemi saklayabilir; ör. google-vertex). Bunlar ZDR sayılmaz: kontrol yalnız safety_retention=false
  uç noktalara bakar, o sağlayıcılar da isteğe provider.ignore olarak yazılır (zdr: true tek başına onları dışlamıyor).
- Buluta yalnız sorgu metni ve seçilmiş parçalar gider. Kullanıcı kimliği, yetki bilgisi, ses, doküman tamamı gönderilmez.
- Anahtar yalnız OPENROUTER_API_KEY ortam değişkeninden okunur, hiçbir yere yazılmaz.
"""
import os
from collections.abc import Callable
from functools import lru_cache
from typing import Any

from .config import OPENROUTER_URL

ZDR_PROVIDER = {"zdr": True, "data_collection": "deny"}
# require_zdr'nin kaydettiği, model başına dışlanacak sağlayıcılar (Safety Retention uç noktası olanlar)
_IGNORE: dict[str, tuple[str, ...]] = {}


def openrouter_body(body: dict[str, Any]) -> dict[str, Any]:
    """İstek gövdesi + zorunlu sağlayıcı kısıtı. Gövdede provider varsa kısıt yine uygulanır (diğer alanları korunur);
    modelin Safety Retention sağlayıcıları çağıranın ignore listesine eklenir."""
    provider = {**(body.get("provider") or {}), **ZDR_PROVIDER}
    ignore = set(provider.get("ignore") or ()) | set(_IGNORE.get(body.get("model", ""), ()))
    if ignore:
        provider["ignore"] = sorted(ignore)
    return {**body, "provider": provider}


RETRY_STATUS = {429, 500, 502, 503, 504}
RETRIES = 4                 # geçici hatalarda (aşırı yük, hız sınırı) en fazla bu kadar yeniden deneme


def post_with_retry(session, url: str, body: dict[str, Any], timeout: float, retries: int = RETRIES,
                    backoff: float = 1.0, sleep=None) -> tuple[Any, int]:
    """POST; 429/5xx ve bağlantı hatasında artan beklemeyle (1, 2, 4, 8 sn) yeniden dener. Döner: (yanıt, deneme sayısı).
    Kalıcı hatalar (400, 401, 404 ZDR reddi) denenmez, çağıran ele alır."""
    import time

    import requests
    sleep = sleep or time.sleep
    for attempt in range(retries + 1):
        try:
            r = session.post(url, json=body, timeout=timeout)
        except (requests.ConnectionError, requests.Timeout):
            if attempt == retries:
                raise
        else:
            if r.status_code not in RETRY_STATUS or attempt == retries:
                return r, attempt + 1
        sleep(backoff * 2 ** attempt)
    raise AssertionError("ulaşılmaz")


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


def strict_zdr(endpoint: dict[str, Any]) -> bool:
    """Gerçek ZDR uç noktası: safety_retention açıkça false. Alan yoksa ZDR sayılmaz."""
    return endpoint.get("safety_retention") is False


def provider_slug(endpoint: dict[str, Any]) -> str:
    """Uç nokta etiketinin sağlayıcı kısmı ("google-vertex/global" → "google-vertex"): provider.ignore bu adı alır."""
    return (endpoint.get("tag") or endpoint.get("provider_name") or "").split("/")[0]


@lru_cache(maxsize=1)
def zdr_index() -> dict[str, dict[str, frozenset[str]]]:
    """Model → {"strict": ZDR sağlayıcıları, "safety": Safety Retention sağlayıcıları} (süreç başına bir kez, ücretsiz uç).
    Aynı sağlayıcının modelde Safety Retention uç noktası varsa o sağlayıcı ZDR sayılmaz (temkinli)."""
    raw: dict[str, dict[str, set[str]]] = {}
    for e in _fetch_zdr_endpoints():
        if e.get("model_id"):
            d = raw.setdefault(e["model_id"], {"strict": set(), "safety": set()})
            d["strict" if strict_zdr(e) else "safety"].add(provider_slug(e))
    return {m: {"strict": frozenset(d["strict"] - d["safety"]), "safety": frozenset(d["safety"])}
            for m, d in raw.items()}


def zdr_model_ids() -> frozenset[str]:
    """En az bir gerçek ZDR (Safety Retention'sız) uç noktası olan modeller."""
    return frozenset(m for m, d in zdr_index().items() if d["strict"])


def require_zdr(model: str, index: Callable[[], dict[str, dict[str, frozenset[str]]]] = zdr_index) -> None:
    """Modelin gerçek ZDR uç noktası yoksa hata. Varsa Safety Retention sağlayıcıları bu modelin isteklerinde dışlanır."""
    d = index().get(model)
    if not d or not d["strict"]:
        why = "yalnız Safety Retention uç noktası var" if d else "ZDR uyumlu sağlayıcısı yok"
        raise ValueError(f"{model}: {why}; ZDR zorunlu olduğu için kullanılamaz ve ölçülmez")
    _IGNORE[model] = tuple(sorted(d["safety"]))


# ---------- embedding (OpenAI uyumlu /embeddings) ----------

class EmbedCache:
    """Bulut embedding önbelleği (SQLite, data/bench_cache/, git dışı): aynı metin aynı model+boyutla iki kez gönderilmez."""

    def __init__(self, path=None) -> None:
        import sqlite3

        from .config import DATA_DIR
        path = path or DATA_DIR / "bench_cache" / "embed_cache.sqlite"
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.execute("CREATE TABLE IF NOT EXISTS v (model TEXT, dim INTEGER, h TEXT, vec BLOB, PRIMARY KEY (model, dim, h))")

    @staticmethod
    def key(text: str) -> str:
        import hashlib
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, model: str, dim: int, texts: list[str]) -> list[list[float] | None]:
        import numpy as np
        out: list[list[float] | None] = []
        for t in texts:
            row = self.db.execute("SELECT vec FROM v WHERE model=? AND dim=? AND h=?",
                                  (model, dim, self.key(t))).fetchone()
            out.append(np.frombuffer(row[0], dtype=np.float32).tolist() if row else None)
        return out

    def put(self, model: str, dim: int, texts: list[str], vecs: list[list[float]]) -> None:
        import numpy as np
        self.db.executemany("INSERT OR REPLACE INTO v VALUES (?, ?, ?, ?)",
                            [(model, dim, self.key(t), np.asarray(v, dtype=np.float32).tobytes())
                             for t, v in zip(texts, vecs)])
        self.db.commit()


class CloudEmbedder:
    """OpenRouter embedding istemcisi. stats: istek sayısı, token, maliyet (API'nin usage alanı), ağ süresi.
    dimensions verilirse API'den istenir (MRL); 0/None: modelin tam boyutu."""

    def __init__(self, model: str, dimensions: int | None = None, batch: int = 64, timeout: float = 120.0,
                 cache: EmbedCache | None = None) -> None:
        import requests
        require_zdr(model)
        self.model, self.dimensions, self.batch, self.timeout = model, dimensions, batch, timeout
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"})
        self.stats = {"requests": 0, "prompt_tokens": 0, "cost_usd": 0.0, "network_s": 0.0, "cached": 0, "retries": 0}
        self.last_network_s = 0.0

    def _call(self, texts: list[str]) -> list[list[float]]:
        import time
        body = {"model": self.model, "input": texts, "encoding_format": "float"}
        if self.dimensions:
            body["dimensions"] = self.dimensions
        t = time.perf_counter()
        r, attempts = post_with_retry(self.session, f"{OPENROUTER_URL}/embeddings", openrouter_body(body), self.timeout)
        self.last_network_s = time.perf_counter() - t
        self.stats["retries"] += attempts - 1
        self.stats["network_s"] += self.last_network_s
        self.stats["requests"] += 1
        if r.status_code != 200:
            raise RuntimeError(f"OpenRouter embeddings {self.model} {r.status_code}: {r.text[:300]}")
        data = r.json()
        usage = data.get("usage") or {}
        self.stats["prompt_tokens"] += int(usage.get("prompt_tokens") or usage.get("total_tokens") or 0)
        self.stats["cost_usd"] += float(usage.get("cost") or 0.0)
        return [d["embedding"] for d in sorted(data["data"], key=lambda d: d["index"])]

    def embed(self, texts: list[str], use_cache: bool = True) -> list[list[float]]:
        dim = self.dimensions or 0
        got = self.cache.get(self.model, dim, texts) if (self.cache and use_cache) else [None] * len(texts)
        missing = [i for i, v in enumerate(got) if v is None]
        self.stats["cached"] += len(texts) - len(missing)
        for start in range(0, len(missing), self.batch):
            idx = missing[start:start + self.batch]
            vecs = self._call([texts[i] for i in idx])
            for i, v in zip(idx, vecs):
                got[i] = v
            if self.cache:
                self.cache.put(self.model, dim, [texts[i] for i in idx], vecs)
        return got  # type: ignore[return-value]


# ---------- sohbet (OpenAI uyumlu /chat/completions) ----------

class CloudChat:
    """OpenRouter sohbet istemcisi (ör. sorgu çevirisi). ZDR zorunlu (require_zdr + openrouter_body).
    stats: istek, token, maliyet (API'nin usage alanı), ağ süresi; last_network_s: son çağrının süresi."""

    def __init__(self, model: str, timeout: float = 60.0) -> None:
        import requests
        require_zdr(model)
        self.model, self.timeout = model, timeout
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"})
        self.stats = {"requests": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "network_s": 0.0,
                      "retries": 0}
        self.last_network_s = 0.0

    def complete(self, messages: list[dict[str, str]], max_tokens: int = 300, temperature: float = 0.0,
                 json_mode: bool = False) -> str:
        import time
        body: dict[str, Any] = {"model": self.model, "messages": messages, "max_tokens": max_tokens,
                                "temperature": temperature, "usage": {"include": True}}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        t = time.perf_counter()
        r, attempts = post_with_retry(self.session, f"{OPENROUTER_URL}/chat/completions", openrouter_body(body),
                                      self.timeout)
        self.last_network_s = time.perf_counter() - t
        self.stats["requests"] += 1
        self.stats["retries"] += attempts - 1
        self.stats["network_s"] += self.last_network_s
        if r.status_code != 200:
            raise RuntimeError(f"OpenRouter chat {self.model} {r.status_code}: {r.text[:300]}")
        data = r.json()
        usage = data.get("usage") or {}
        self.stats["prompt_tokens"] += int(usage.get("prompt_tokens") or 0)
        self.stats["completion_tokens"] += int(usage.get("completion_tokens") or 0)
        self.stats["cost_usd"] += float(usage.get("cost") or 0.0)
        return data["choices"][0]["message"]["content"] or ""
