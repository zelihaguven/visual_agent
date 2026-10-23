"""OpenRouter: anahtar kontrolü (kullanım/limit), güncel embedding/rerank modelleri ve ZDR uyumlu sağlayıcıları. Ücretsiz uçlar.

Kullanım: python -m bench.openrouter_models   -> eval/bench/openrouter_modeller_<tarih>.json
Anahtar yalnız OPENROUTER_API_KEY ortam değişkeninden okunur, hiçbir yere yazılmaz.
"""
import json
import os
from datetime import datetime

import requests

from bench.common import OUT_DIR
from pilot.config import OPENROUTER_URL


def _get(path: str, key: str) -> dict:
    r = requests.get(f"{OPENROUTER_URL}{path}", headers={"Authorization": f"Bearer {key}"}, timeout=30)
    return {"status": r.status_code, "body": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:300]}


def main() -> None:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY tanımlı değil")
    info = _get("/key", key)
    data = info["body"].get("data", {}) if isinstance(info["body"], dict) else {}
    print("anahtar:", info["status"], {k: data.get(k) for k in ("label", "usage", "limit", "limit_remaining",
                                                                  "is_free_tier")})
    out = {"date": datetime.now().isoformat(timespec="seconds"), "key_status": info["status"]}
    for kind, path in (("embeddings", "/embeddings/models"), ("rerank", "/models?output_modalities=rerank"),
                       ("all", "/models")):
        res = _get(path, key)
        models = res["body"].get("data", []) if isinstance(res["body"], dict) else []
        out[kind] = {"status": res["status"], "models": [
            {k: m.get(k) for k in ("id", "name", "context_length", "pricing", "architecture", "description")}
            for m in models] if kind != "all" else [{k: m.get(k) for k in ("id", "pricing")}
            for m in models]}
        print(kind, res["status"], len(models))
    zdr = _get("/endpoints/zdr", key)
    zdr_list = zdr["body"].get("data", []) if isinstance(zdr["body"], dict) else []
    zdr_models: dict[str, list[str]] = {}
    for e in zdr_list:
        zdr_models.setdefault(e.get("model_id"), []).append(e.get("provider_name"))
    out["zdr"] = {"status": zdr["status"], "n_endpoints": len(zdr_list)}
    for kind in ("embeddings", "rerank"):
        for m in out[kind]["models"]:
            m["zdr_providers"] = zdr_models.get(m["id"], [])
    out["rerank_like"] = out["rerank"]["models"]
    out["embed_like"] = [m for m in out["all"]["models"] if "embed" in (m["id"] or "").lower()
                         or "bge" in (m["id"] or "").lower()]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"openrouter_modeller_{datetime.now():%Y-%m-%d}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for m in out["rerank_like"]:
        print("rerank:", m["id"], "ZDR:", m["zdr_providers"] or "YOK")
    for m in out["embeddings"]["models"]:
        print("embed:", m["id"], (m.get("pricing") or {}).get("prompt"), m.get("context_length"),
              "ZDR:", m["zdr_providers"] or "YOK")
    print(path)


if __name__ == "__main__":
    main()
