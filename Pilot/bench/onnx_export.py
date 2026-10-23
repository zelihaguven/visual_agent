"""Reranker'ı ONNX'e aktar ve dinamik int8 quantization uygula (CPU süresi denemesi).

Kullanım (Pilot klasöründe): python -m bench.onnx_export BAAI/bge-reranker-v2-m3
Çıktı: data/bench_cache/onnx/<model>/model.onnx (+ .data, 2 GB üstü ağırlıklar ayrı dosyada) ve model_int8.onnx.
Git dışı. Kullanmak için: PILOT_RERANK_BACKEND=onnx | onnx-int8.
"""
import logging
import sys
import time
import warnings

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("onnx_export")


def export(model: str) -> None:
    import torch
    from onnxruntime.quantization import QuantType, quantize_dynamic
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    from pilot.rerankers import _trust, onnx_path

    out = onnx_path(model, int8=False)
    out.parent.mkdir(parents=True, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(model, trust_remote_code=_trust(model))
    m = AutoModelForSequenceClassification.from_pretrained(model, trust_remote_code=_trust(model)).eval()
    enc = tok(["örnek soru"] * 2, ["örnek parça metni, biraz daha uzun", "kısa"], padding=True, return_tensors="pt")
    names = [k for k in ("input_ids", "attention_mask", "token_type_ids") if k in enc]
    axes = {k: {0: "batch", 1: "seq"} for k in names}
    axes["logits"] = {0: "batch"}

    class Wrap(torch.nn.Module):
        def __init__(self, inner):
            super().__init__()
            self.inner = inner

        def forward(self, *args):
            return self.inner(**dict(zip(names, args))).logits

    t = time.time()
    with torch.inference_mode():
        torch.onnx.export(Wrap(m), tuple(enc[k] for k in names), str(out), input_names=names,
                          output_names=["logits"], dynamic_axes=axes, opset_version=17, dynamo=False,
                          external_data=True)
    log.info("ONNX: %s (%.0f sn)", out, time.time() - t)
    t = time.time()
    quantize_dynamic(str(out), str(onnx_path(model, int8=True)), weight_type=QuantType.QInt8,
                     use_external_data_format=False)
    log.info("int8: %s (%.0f sn)", onnx_path(model, int8=True), time.time() - t)


if __name__ == "__main__":
    for name in sys.argv[1:] or ["BAAI/bge-reranker-v2-m3"]:
        export(name)
