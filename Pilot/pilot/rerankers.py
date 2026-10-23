"""Reranker sağlayıcıları. Hepsi aynı arayüzde: reranker(query, passages) -> skorlar (passages sırasıyla).

- torch:     varsayılan; model doğrudan transformers ile. FlagEmbedding her çağrıda ilk batch'i batch boyutu denemesi için
             bir kez fazladan hesaplıyor; 20 aday tek batch'e sığdığı için iş iki kez yapılıyordu (BENCHMARK-RAPORU)
- flag:      FlagEmbedding FlagReranker (pilotun ilk varsayılanı, aynı skor)
- onnx:      aynı model ONNX Runtime ile (bench/onnx_export.py dışa aktarır); onnx-int8: dinamik int8 quantization
- openrouter: bulut rerank (Cohere uyumlu /rerank ucu); ZDR zorunlu, anahtar yalnız OPENROUTER_API_KEY'den (cloud.py)
"""
import re
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from .cloud import api_key, openrouter_body, require_zdr
from .config import DATA_DIR, EMBED_DEVICE, OPENROUTER_URL, TORCH_THREADS

Reranker = Callable[[str, Sequence[str]], list[float]]
ONNX_DIR = DATA_DIR / "bench_cache" / "onnx"


def model_slug(model: str) -> str:
    return re.sub(r"[^\w.-]+", "--", model)


def onnx_path(model: str, int8: bool) -> Path:
    return ONNX_DIR / model_slug(model) / ("model_int8.onnx" if int8 else "model.onnx")


def length_batches(lengths: Sequence[int], batch_size: int) -> list[list[int]]:
    """Uzunluğa göre sıralı indeks grupları: aynı batch'teki dizilerin dolgu (padding) payı küçük kalır."""
    order = sorted(range(len(lengths)), key=lambda i: -lengths[i])
    return [order[i:i + batch_size] for i in range(0, len(order), batch_size)]


def _set_threads() -> None:
    if TORCH_THREADS:
        import torch
        torch.set_num_threads(TORCH_THREADS)


def _trust(model: str) -> bool:
    return "jina" in model.lower() or "gte" in model.lower()


def _compat_remote_code() -> None:
    """jina-reranker-v2'nin uzak kodu transformers 5'te kaldırılan bir yardımcıyı içe aktarıyor; aynısı eklenir."""
    import torch
    from transformers.models.xlm_roberta import modeling_xlm_roberta as xr
    if hasattr(xr, "create_position_ids_from_input_ids"):
        return

    def create_position_ids_from_input_ids(input_ids, padding_idx, past_key_values_length=0):
        mask = input_ids.ne(padding_idx).int()
        return ((torch.cumsum(mask, dim=1).type_as(mask) + past_key_values_length) * mask).long() + padding_idx

    xr.create_position_ids_from_input_ids = create_position_ids_from_input_ids


class FlagRerank:
    def __init__(self, model: str, max_length: int, **_: Any) -> None:
        from FlagEmbedding import FlagReranker
        _set_threads()
        self.max_length = max_length
        self._m = FlagReranker(model, use_fp16=False, devices=[EMBED_DEVICE])

    def __call__(self, query: str, passages: Sequence[str]) -> list[float]:
        scores = self._m.compute_score([[query, p] for p in passages], max_length=self.max_length)
        return [float(s) for s in (scores if isinstance(scores, list) else [scores])]


class _Tokenized:
    def __init__(self, model: str, max_length: int, batch_size: int) -> None:
        from transformers import AutoTokenizer
        self.tok = AutoTokenizer.from_pretrained(model, trust_remote_code=_trust(model))
        self.max_length, self.batch_size = max_length, batch_size

    def batches(self, query: str, passages: Sequence[str]):
        enc = self.tok([query] * len(passages), list(passages), truncation="only_second",
                       max_length=self.max_length)
        for idx in length_batches([len(x) for x in enc["input_ids"]], self.batch_size):
            feats = [{k: enc[k][i] for k in enc} for i in idx]
            yield idx, self.tok.pad(feats, padding=True, return_tensors="np")


class TorchRerank(_Tokenized):
    def __init__(self, model: str, max_length: int, batch_size: int = 8, **_: Any) -> None:
        import torch
        from transformers import AutoModelForSequenceClassification
        super().__init__(model, max_length, batch_size)
        _set_threads()
        if _trust(model):
            _compat_remote_code()
        self.torch = torch
        # Açıkça float32: transformers 5 varsayılanı dtype="auto" (jina bf16, gte fp16 yükleniyordu); bu CPU'da bf16/fp16
        # hızlandırması yok, jina 54 sn sürüyordu (BENCHMARK-RAPORU Aşama 1)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model, trust_remote_code=_trust(model), dtype=torch.float32).eval()

    def __call__(self, query: str, passages: Sequence[str]) -> list[float]:
        out = [0.0] * len(passages)
        with self.torch.inference_mode():
            for idx, b in self.batches(query, passages):
                logits = self.model(**{k: self.torch.from_numpy(v) for k, v in b.items()}).logits
                for i, s in zip(idx, logits[:, 0].float().tolist()):
                    out[i] = s
        return out


class OnnxRerank(_Tokenized):
    def __init__(self, model: str, max_length: int, batch_size: int = 8, int8: bool = False, **_: Any) -> None:
        import onnxruntime as ort
        super().__init__(model, max_length, batch_size)
        path = onnx_path(model, int8)
        if not path.exists():
            raise FileNotFoundError(f"{path} yok: önce python -m bench.onnx_export {model}")
        so = ort.SessionOptions()
        if TORCH_THREADS:
            so.intra_op_num_threads = TORCH_THREADS
        self.sess = ort.InferenceSession(str(path), so, providers=["CPUExecutionProvider"])
        self.inputs = {i.name for i in self.sess.get_inputs()}

    def __call__(self, query: str, passages: Sequence[str]) -> list[float]:
        out = [0.0] * len(passages)
        for idx, b in self.batches(query, passages):
            feed = {k: v.astype("int64") for k, v in b.items() if k in self.inputs}
            logits = self.sess.run(None, feed)[0]
            for i, s in zip(idx, logits[:, 0].tolist()):
                out[i] = float(s)
        return out


class OpenRouterRerank:
    """Cohere uyumlu rerank ucu, ZDR zorunlu (cloud.py). last_network_s: son çağrının istek-cevap süresi (ağ + sunucu)."""

    def __init__(self, model: str, timeout: float = 60.0, **_: Any) -> None:
        import requests
        key = api_key()
        require_zdr(model)
        self.model, self.timeout = model, timeout
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        self.last_network_s = 0.0
        self.last_usage: dict[str, Any] = {}

    def __call__(self, query: str, passages: Sequence[str]) -> list[float]:
        t = time.perf_counter()
        r = self.session.post(f"{OPENROUTER_URL}/rerank", timeout=self.timeout,
                              json=openrouter_body({"model": self.model, "query": query, "documents": list(passages),
                                                    "top_n": len(passages)}))
        self.last_network_s = time.perf_counter() - t
        if r.status_code != 200:
            # Hata metni loga gider; istek başlıkları (anahtar) yazılmaz
            raise RuntimeError(f"OpenRouter rerank {r.status_code}: {r.text[:300]}")
        body = r.json()
        self.last_usage = body.get("usage") or body.get("meta") or {}
        return parse_rerank_response(body, len(passages))


def parse_rerank_response(body: dict[str, Any], n: int) -> list[float]:
    """{'results': [{'index': i, 'relevance_score': s}, ...]} → passages sırasıyla skor (dönmeyenler -inf)."""
    out = [float("-inf")] * n
    for r in body.get("results") or body.get("data") or []:
        score = r.get("relevance_score", r.get("score"))
        out[int(r["index"])] = float(score)
    return out


def make_reranker(provider: str, model: str, backend: str = "flag", max_length: int = 512,
                  batch_size: int = 8) -> Reranker:
    if provider == "openrouter":
        return OpenRouterRerank(model)
    if provider != "local":
        raise ValueError(f"bilinmeyen rerank sağlayıcısı: {provider}")
    if backend == "flag":
        return FlagRerank(model, max_length)
    if backend == "torch":
        return TorchRerank(model, max_length, batch_size)
    if backend in ("onnx", "onnx-int8"):
        return OnnxRerank(model, max_length, batch_size, int8=backend == "onnx-int8")
    raise ValueError(f"bilinmeyen rerank backend'i: {backend}")
