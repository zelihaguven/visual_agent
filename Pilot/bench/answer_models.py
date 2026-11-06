"""Adım 2: cevap modeli seçimi, ilk tur (plan: eval/bench/adim2/plan_cevap_modeli_2026-11-05.md).

Arama sabit: uygulamanın varsayılan yolu (pipeline.soru_cevapla; bge-m3 + BM25, rerank kapalı, ilke dışı kurallar
kapalı). Arama sonuçları bir kez hesaplanıp dosyaya yazılır (data/bench_cache/adim2_arama.json); bütün modeller aynı
kaynakları görür. Yalnız pipeline.chat_json ölçüm aracında modele yönlendirilir; uygulamaya bir şey bağlanmaz.

Bütün modellerde aynı sistem talimatı (pilot.prompts.SYSTEM_PROMPT), aynı şema (ANSWER_SCHEMA, response_format
json_schema, strict değil), temperature 0, max_tokens LLM_NUM_PREDICT; modele özel istem ayarı yok. Düşünme kapalı
(reasoning effort none ya da enabled false; koşu öncesi bir kontrol çağrısıyla doğrulanır). Bulut modelleri tek
sağlayıcıya sabitlenir (provider.order, allow_fallbacks false; ZDR kısıtı ve Safety Retention dışlaması cloud.py'den).
Yeniden deneme politikası bütün modellerde aynı: ilk token gelmeden 429/5xx/bağlantı hatasında 30 sn bekleyip bir kez
yeniden; yine olmazsa soru "cevapsız" (kalite metriklerine girmez, dayanıklılıkta sayılır).

Kullanım (Pilot klasöründe, Qdrant sunucusu açık):
    python -m bench.answer_models --prepare                       # arama + kural çıkışları (bulut yok)
    python -m bench.answer_models --models gemma4 qwen36 gpt54mini mistral2603 --max-usd 1.5
    python -m bench.answer_models --models qwen25_7b              # yerel taban (Ollama)
    python -m bench.answer_models --models gemma4 ... --n 30 --tag sure2   # ikinci süre turu
    python -m bench.answer_models --report
"""
import argparse
import json
import random
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from bench.common import (KNOWN_SETS, PILOT_DIR, first_rank, is_match, load_questions, percentile, sse_events,
                          value_in, variants_in,
                          write_result)

CACHE = PILOT_DIR / "data" / "bench_cache" / "adim2_arama.json"
RAW_DIR = PILOT_DIR / "eval" / "bench" / "adim2" / "ham"
SETS = [*KNOWN_SETS, "aday_sorular"]            # JUKI (ayrı tutulan doğrulama seti) yok
RETRY_WAIT = 30.0
# Rozeti veren verify.py sürümü; ham dosyaya yazılır. Önceki sürümle puanlanmış kayıtlar --rescore ile yeniden puanlanır.
VERIFY_TAG = "A+B (2026-11-05): çoklu atıf, liste numarası, değer biçimi, alıntıda yazıyla sayı"
# Beklenen değer eşleştiricisi sürümü (bench.common.value_in); değişince --rescore deger_dogru'yu yeniden hesaplar.
VALUE_TAG = "değer olarak, 2026-11-05"
MODELS: dict[str, dict[str, Any]] = {
    "gemma4": {"id": "google/gemma-4-26b-a4b-it", "provider": "deepinfra", "reasoning": {"enabled": False}},
    "qwen36": {"id": "qwen/qwen3.6-35b-a3b", "provider": "deepinfra", "reasoning": {"enabled": False}},
    "gpt54mini": {"id": "openai/gpt-5.4-mini", "provider": "azure", "reasoning": {"effort": "none"}},
    "mistral2603": {"id": "mistralai/mistral-small-2603", "provider": "mistral", "reasoning": {"effort": "none"}},
    "qwen25_7b": {"id": "qwen2.5:7b", "provider": "yerel (Ollama)", "local": True},
    # Nihai tur (plan §12, §18): Gemma 4'ün bf16 sağlayıcıları ve üst sınıf referans Gemma 4 31B (bf16)
    "gemma4_nextbit": {"id": "google/gemma-4-26b-a4b-it", "provider": "nextbit", "quant": "bf16",
                       "reasoning": {"enabled": False}},
    "gemma4_parasail": {"id": "google/gemma-4-26b-a4b-it", "provider": "parasail", "quant": "bf16",
                        "reasoning": {"enabled": False}},
    "gemma4_venice": {"id": "google/gemma-4-26b-a4b-it", "provider": "venice", "quant": "bf16",
                      "reasoning": {"enabled": False}},
    "gemma4_31b": {"id": "google/gemma-4-31b-it", "provider": "crusoe", "quant": "bf16", "reasoning": {"enabled": False}},
}
# Cevap şeması: "bugun" (pilot.prompts.ANSWER_SCHEMA) ya da "c" (bench.schema_c; plan §15.0). --schema ile seçilir.
SCHEMA = "bugun"


MAX_TOKENS = 0          # 0: uygulamanın LLM_NUM_PREDICT değeri; --max-tokens ile deneme (devir d/3)
ONLY_IDS: list[str] = []   # --ids: yalnız bu soru kimlikleri (deneme)


def schema_and_prompt() -> tuple[dict[str, Any], str]:
    from pilot.prompts import ANSWER_SCHEMA, SYSTEM_PROMPT
    if SCHEMA.startswith("c"):
        from bench.schema_c import schema_variant
        return schema_variant(SCHEMA)
    return ANSWER_SCHEMA, SYSTEM_PROMPT
# Ayrıştırıcının attığı düşünce blokları (boş ya da dolu): <think>…</think>, <thought>…</thought>, Gemma kanal işaretleri
THOUGHT = re.compile(r"^\s*(?:<think>.*?</think>|<thought>.*?</thought>|<\|?channel\|?>[^{]*?<\|?channel\|?>|"
                     r"<\|?channel\|?>thought[^{]*)\s*", re.S)


class Unanswered(Exception):
    """Sağlayıcı hatası (yeniden denemeden sonra da): soru cevapsız kaldı."""


class Budget(Exception):
    pass


def parse_answer(content: str, finish: str | None) -> tuple[dict[str, Any] | None, str, bool]:
    """(cevap, json durumu, düşünce bloğu atıldı mı). Durum: ok | bos | kesik | gecersiz | sema_disi."""
    from pilot.prompts import ANSWER_SCHEMA
    text = content or ""
    stripped = THOUGHT.sub("", text, count=1)
    thought = stripped != text
    start = stripped.find("{")
    if not stripped.strip():
        return None, "bos", thought
    if start < 0:
        return None, ("kesik" if finish == "length" else "gecersiz"), thought
    try:
        from pilot.jsonparse import raw_decode
        obj, _ = raw_decode(stripped[start:])            # strict=False: ortak ayrıştırma adımı (2026-11-06)
    except json.JSONDecodeError:
        return None, ("kesik" if finish == "length" else "gecersiz"), thought
    if start > 0 and stripped[:start].strip():
        thought = True                                   # JSON'dan önce başka metin (ör. kod çiti) atıldı
    if not isinstance(obj, dict) or any(k not in obj for k in ANSWER_SCHEMA["required"]):
        return obj if isinstance(obj, dict) else None, "sema_disi", thought
    return obj, "ok", thought


class CloudModel:
    """Akışlı çağrı, tek sağlayıcı, aynı yeniden deneme politikası. last: son sorunun çağrı kaydı."""

    def __init__(self, key: str) -> None:
        import requests

        from pilot.cloud import api_key, require_zdr, zdr_index
        self.key, self.spec = key, MODELS[key]
        require_zdr(self.spec["id"])
        strict = zdr_index()[self.spec["id"]]["strict"]
        if self.spec["provider"] not in strict:
            raise ValueError(f"{self.spec['id']}: {self.spec['provider']} ZDR sağlayıcısı değil ({sorted(strict)})")
        self.zdr_providers = sorted(strict)
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"})
        self.last: dict[str, Any] = {}

    def body(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        from pilot.cloud import openrouter_body
        from pilot.config import LLM_NUM_PREDICT
        schema = schema_and_prompt()[0]
        provider = {"order": [self.spec["provider"]], "allow_fallbacks": False}
        if self.spec.get("quant"):
            provider["quantizations"] = [self.spec["quant"]]
        return openrouter_body({
            "model": self.spec["id"], "messages": messages, "temperature": 0, "max_tokens": MAX_TOKENS or LLM_NUM_PREDICT,
            "stream": True, "usage": {"include": True}, "reasoning": self.spec["reasoning"],
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": "cevap", "strict": False, "schema": schema}},
            "provider": provider})

    def stream(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        from pilot.config import OPENROUTER_URL
        rec: dict[str, Any] = {"attempts": [], "content": "", "reasoning_text": "", "zaman": []}
        for attempt in range(2):
            t0 = time.perf_counter()
            err, first = "", None
            try:
                with self.session.post(f"{OPENROUTER_URL}/chat/completions", json=self.body(messages), stream=True,
                                       timeout=(10, 120)) as r:
                    if r.status_code != 200:
                        err = f"{r.status_code}: {r.text[:200]}"
                    else:
                        for d in sse_events(r):
                            if d.get("error"):
                                err = f"akış hatası: {json.dumps(d['error'])[:200]}"
                                break
                            rec["provider"] = d.get("provider") or rec.get("provider")
                            if d.get("usage"):
                                rec["usage"] = d["usage"]
                            ch = (d.get("choices") or [{}])[0]
                            delta = ch.get("delta") or {}
                            if delta.get("reasoning"):
                                rec["reasoning_text"] += delta["reasoning"]
                            if delta.get("content"):
                                if first is None:
                                    first = time.perf_counter() - t0
                                rec["content"] += delta["content"]
                                # akış zaman çizelgesi: [istekten sn, o ana kadarki karakter] (ilk doğrulanmış cümle)
                                rec["zaman"].append([round(time.perf_counter() - t0, 3), len(rec["content"])])
                            if ch.get("finish_reason"):
                                rec["finish"] = ch["finish_reason"]
            except Exception as e:  # noqa: BLE001 — bağlantı/zaman aşımı
                err = repr(e)[:200]
            rec["attempts"].append({"err": err, "sn": time.perf_counter() - t0})
            if not err or rec["content"]:
                rec.update(first_token=first, total=time.perf_counter() - t0)
                return rec
            transient = err[:3] in ("429", "500", "502", "503", "504") or not err[:3].isdigit()
            if attempt == 0 and transient:
                time.sleep(RETRY_WAIT)
                continue
            break
        rec["unanswered"] = rec["attempts"][-1]["err"]
        return rec

    def cost(self, rec: dict[str, Any]) -> float:
        return float((rec.get("usage") or {}).get("cost") or 0.0)


class LocalModel:
    """Yerel taban (Ollama, pilot.llm ile aynı ayarlar: format=ANSWER_SCHEMA, num_ctx, num_predict), akışlı."""

    zdr_providers = ["yerel"]

    def __init__(self, key: str) -> None:
        self.key, self.spec = key, MODELS[key]

    def stream(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        import ollama

        from pilot.config import LLM_NUM_CTX, LLM_NUM_PREDICT
        schema = schema_and_prompt()[0]
        rec: dict[str, Any] = {"attempts": [], "content": "", "reasoning_text": "", "provider": "yerel", "zaman": []}
        t0, first = time.perf_counter(), None
        try:
            for part in ollama.chat(model=self.spec["id"], messages=messages, format=schema, stream=True,
                                    options={"temperature": 0, "num_ctx": LLM_NUM_CTX, "num_predict": LLM_NUM_PREDICT},
                                    keep_alive="30m"):
                piece = part["message"]["content"]
                if piece and first is None:
                    first = time.perf_counter() - t0
                rec["content"] += piece
                if piece:
                    rec["zaman"].append([round(time.perf_counter() - t0, 3), len(rec["content"])])
                if part.get("done"):
                    rec["finish"] = "length" if part.get("done_reason") == "length" else "stop"
                    rec["usage"] = {"prompt_tokens": part.get("prompt_eval_count"),
                                    "completion_tokens": part.get("eval_count"), "cost": 0.0}
        except Exception as e:  # noqa: BLE001
            rec["unanswered"] = repr(e)[:200]
        rec["attempts"].append({"err": rec.get("unanswered", ""), "sn": time.perf_counter() - t0})
        rec.update(first_token=first, total=time.perf_counter() - t0)
        return rec

    def cost(self, rec: dict[str, Any]) -> float:
        return 0.0


# ---------- arama önbelleği (bütün modeller aynı kaynakları görür) ----------

def _hit_to_json(h: Any) -> dict[str, Any]:
    return {"chunk": h.chunk, "fused_rank": h.fused_rank, "rerank_score": h.rerank_score, "fused_score": h.fused_score}


def install_search_cache(frozen: bool) -> dict[str, Any]:
    """pipeline.search'ü dosya önbellekli sarmalla değiştirir. frozen: önbellekte olmayan arama hata verir."""
    from pilot import pipeline, retrieve
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}

    def search(query: str, **kw: Any) -> list[Any]:
        key = json.dumps([query, kw.get("brands"), kw.get("doc_ids"), kw.get("top_k")], ensure_ascii=False)
        if key not in cache:
            if frozen:
                raise RuntimeError(f"arama önbellekte yok (önce --prepare): {key}")
            cache[key] = [_hit_to_json(h) for h in retrieve.search(query, **kw)]
        return [retrieve.Hit(**h) for h in cache[key]]

    pipeline.search = search
    return cache


def questions(include_clarify: bool = False) -> list[dict[str, Any]]:
    """Modele gidebilecek sorular: cevaplı + "bulunamadı"; include_clarify ile netleştirme beklenenler de (nihai tur)."""
    return [q for q in load_questions(SETS, include_unapproved=True) if include_clarify or not q.get("expect_clarify")]


def prepare() -> None:
    """Arama ve kural çıkışları, model çağrılmadan (bulut yok). Arama önbelleği ve kural çıkışları yazılır."""
    from pilot import config, pipeline
    cache = install_search_cache(frozen=False)

    def stop(_user: str) -> Any:
        raise _Reached

    pipeline.chat_json = stop
    path = RAW_DIR / "kural_cikislari.json"      # önceki setlerin kayıtları korunur (birleştirilir)
    rules = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for q in questions(include_clarify=True):      # nihai tur netleştirme sorularını da kapsar
        try:
            res = pipeline.soru_cevapla(q["q"])
            rules[q["qid"]] = rule_exit(res)
        except _Reached:
            rules[q["qid"]] = None
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    (RAW_DIR / "kural_cikislari.json").parent.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / "kural_cikislari.json").write_text(json.dumps(rules, ensure_ascii=False, indent=1), encoding="utf-8")
    print("kural çıkışları:", Counter(v or "model" for v in rules.values()), "· arama:", len(cache))


class _Reached(Exception):
    pass


def rule_exit(res: Any) -> str:
    a, why = res.answer, res.answer.get("neden") or ""
    if res.verification.status == "clarify":
        return "netlestirme_sonra" if res.hits else "netlestirme_once"
    if "marka" in why and "doküman yok" in why:
        return "yabanci_marka"
    if "kodu" in why and "geçmiyor" in why:
        return "kod_yok"
    return "bulunamadi_kural" if a.get("bulunamadi") else "diger"


def spent_all(exclude: Path | None = None, prefix: str | None = None) -> float:
    """Bu Adım 2 turunun bütün koşularının harcaması (ham sonuç dosyalarından; bütçe sınırı toplam için)."""
    total = 0.0
    for f in RAW_DIR.glob(f"{prefix}*_*.json" if prefix else "*_*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if f != exclude and isinstance(d, dict) and isinstance(d.get("cost_usd"), float):
            total += d["cost_usd"]
    return total


def thinking_check(m: Any) -> dict[str, Any]:
    """Düşünmenin kapalı olduğu: düşünce tokeni 0 (ya da alan yok) ve düşünce metni yok."""
    SYSTEM_PROMPT = schema_and_prompt()[1]
    rec = m.stream([{"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": "<kaynaklar>\n</kaynaklar>\n\n<cevap_dili>TR</cevap_dili>\n\n"
                                                "<soru>\nDeneme sorusu: kaynak yok.\n</soru>"}])
    det = (rec.get("usage") or {}).get("completion_tokens_details") or {}
    rt = int(det.get("reasoning_tokens") or 0)
    return {"reasoning_tokens": rt, "reasoning_text": len(rec["reasoning_text"]), "provider": rec.get("provider"),
            "ok": rt == 0 and not rec["reasoning_text"] and not rec.get("unanswered"), "cost": m.cost(rec),
            "err": rec.get("unanswered"), "json": parse_answer(rec["content"], rec.get("finish"))[1]}


def run_model(key: str, tag: str, n: int, max_usd: float, seed: int, clarify: str | None = None) -> Path:
    from pilot import pipeline
    install_search_cache(frozen=True)
    m = LocalModel(key) if MODELS[key].get("local") else CloudModel(key)
    system_prompt = schema_and_prompt()[1]
    # Netleştirme soruları: C'de varsayılan dahil (nihai tur, plan §18); bugünkü şemada varsayılan hariç (ilk tur gibi)
    clarify = clarify or ("dahil" if SCHEMA.startswith("c") else "haric")
    qs = questions(include_clarify=clarify != "haric")
    if clarify == "yalniz":
        qs = [q for q in qs if q.get("expect_clarify")]
    if ONLY_IDS:
        qs = [q for q in qs if q["id"] in ONLY_IDS or q["qid"] in ONLY_IDS]
    if n:
        qs = random.Random(seed).sample([q for q in qs if not q.get("expect_not_found")], n)
    out: dict[str, Any] = {"model": key, "spec": MODELS[key], "tag": tag, "zdr_providers": m.zdr_providers,
                           "verify": VERIFY_TAG, "deger": VALUE_TAG, "sema": SCHEMA, "netlestirme_sorulari": clarify,
                           "max_tokens": MAX_TOKENS or None,
                           "start": datetime.now().isoformat(timespec="seconds"), "rows": {}, "cost_usd": 0.0}
    path = RAW_DIR / f"{tag}_{key}.json"
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    def save() -> None:
        out["end"] = datetime.now().isoformat(timespec="seconds")
        path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    if not MODELS[key].get("local"):
        chk = thinking_check(m)
        out["dusunme_kontrolu"], out["cost_usd"] = chk, chk["cost"]
        print(f"{key}: düşünme kontrolü {chk}", flush=True)
        if not chk["ok"]:
            out["durdu"] = "düşünme kapanmadı ya da kontrol çağrısı başarısız"
            save()
            return path
    current: dict[str, Any] = {}
    # nihai_* turlarının bütçesi ayrı (karar 2026-11-05: 3,0 USD); ön eleme dosyaları sayılmaz
    others = spent_all(exclude=path, prefix="nihai" if tag.startswith("nihai") else None)

    def chat(user: str) -> tuple[dict[str, Any], dict[str, float]]:
        if others + out["cost_usd"] > max_usd:
            raise Budget
        rec = m.stream([{"role": "system", "content": system_prompt}, {"role": "user", "content": user}])
        out["cost_usd"] += m.cost(rec)
        current["rec"] = rec
        if rec.get("unanswered"):
            raise Unanswered(rec["unanswered"])
        if SCHEMA.startswith("c"):
            from bench.schema_c import parse_c, to_legacy
            ans_c, status = parse_c(rec["content"], rec.get("finish"))
            current.update(json=status, thought=False, c=ans_c)
            if status in ("bos", "kesik", "gecersiz") or ans_c is None:
                from pilot.jsonparse import ModelJSONError, error_detail
                raise ModelJSONError(status == "kesik", error_detail(rec["content"] or "") or status)
            return to_legacy(ans_c), {"llm_seconds": rec["total"]}   # pipeline akışı için; puan C'den (judge_c)
        ans, status, thought = parse_answer(rec["content"], rec.get("finish"))
        current.update(json=status, thought=thought)
        if status in ("bos", "kesik", "gecersiz"):
            from pilot.jsonparse import ModelJSONError, error_detail
            raise ModelJSONError(status == "kesik", error_detail(rec["content"] or "") or status)
        return ans, {"llm_seconds": rec["total"]}

    pipeline.chat_json = chat
    for i, q in enumerate(qs, 1):
        current.clear()
        row: dict[str, Any] = {}
        try:
            res = pipeline.soru_cevapla(q["q"])
            row = judge_c(q, res, current) if SCHEMA.startswith("c") and current.get("c") is not None else judge(q, res)
        except Unanswered as e:
            row = {"cikis": "cevapsiz", "hata": str(e)}
        except Budget:
            out["durdu"] = f"bütçe sınırı {max_usd} USD"
            print(f"BÜTÇE SINIRI: {max_usd} USD aşılacaktı, durdu ({key}, {i}/{len(qs)})", flush=True)
            break
        rec = current.get("rec") or {}
        usage = rec.get("usage") or {}
        row.update(json=current.get("json"), dusunce_blogu=current.get("thought"), provider=rec.get("provider"),
                   ilk_token=rec.get("first_token"), toplam=rec.get("total"), finish=rec.get("finish"),
                   denemeler=rec.get("attempts"), giris=usage.get("prompt_tokens"), cikis_token=usage.get("completion_tokens"),
                   dusunce_token=((usage.get("completion_tokens_details") or {}).get("reasoning_tokens")),
                   maliyet=m.cost(rec) if rec else 0.0, ham=rec.get("content", "") if rec else "")
        if SCHEMA.startswith("c") and rec.get("zaman"):
            row["akis_zaman"] = rec["zaman"]     # [[sn, karakter], ...] (2026-11-06)
        out["rows"][q["qid"]] = row
        print(f"{time.strftime('%H:%M:%S')} {key} {i}/{len(qs)} {q['qid']} {row.get('cikis')} "
              f"json={row.get('json')} ilk_token={row.get('ilk_token') or float('nan'):.2f} "
              f"sağlayıcı={row.get('provider')} · {out['cost_usd']:.4f} USD", flush=True)
        if i % 10 == 0:
            save()
    out["tamam"] = not out.get("durdu")
    save()
    return path


CLARIFY_CLASSES = PILOT_DIR / "eval" / "netlestirme_siniflari.json"


def judge_c(q: dict[str, Any], res: Any, current: dict[str, Any]) -> dict[str, Any]:
    """Şema C sonucu (plan §15.0): çıkış modelin "tur"u; rozet öğe başına doğrulamadan; ilk doğrulanmış cümle akıştan;
    netleştirmede seçenekler kaynak numarası → doküman. Pipeline'ın varyant kuralı C'de uygulanmaz (not)."""
    from bench.doc_rules_diff import options_verdict
    from bench.schema_c import first_verified_time, verify_c
    ans, rec = current["c"], current.get("rec") or {}
    chunks = [h.chunk for h in res.hits]
    sources = {no: c["text"] for no, c in enumerate(chunks, start=1)}
    generated = {no: c.get("generated", "") for no, c in enumerate(chunks, start=1)}
    from bench.schema_c import QUOTE_LIMIT
    v = verify_c(ans, sources, generated, QUOTE_LIMIT.get(SCHEMA, 300))
    tur = ans.get("tur")
    row: dict[str, Any] = {"cikis": {"cevap": "cevap", "netlestirme": "netlestirme", "bulunamadi": "bulunamadi"}[tur],
                           "durum": v["status"], "sorunlar": v["problems"][:4], "kaynaklar": [[c["doc_id"], c["pages"]] for c in chunks],
                           "sira": first_rank(chunks, q) if (q.get("expect_docs") or q.get("kabul")) else None,
                           "cevap": " ".join(x.get("metin", "") for x in ans.get("cevap") or [])[:600],
                           "ogeler": [i["ok"] for i in v["items"]]}
    if tur == "cevap":
        row["ilk_dogrulanmis_cumle"] = first_verified_time(rec.get("content", ""), rec.get("zaman") or [], v["items"])
        cited = [n for i in v["items"] for n in i.get("kaynaklar") or [i["kaynak_no"]]]
        ok = [is_match(chunks[n - 1], q) for n in cited if isinstance(n, int) and 1 <= n <= len(chunks)]
        row["atif_dogru_biri"] = any(ok) if ok else None
        row["atif_dogru_hepsi"] = all(ok) if ok else None
        row["atif_dokumanlari"] = sorted({chunks[n - 1]["doc_id"] for n in cited if isinstance(n, int) and 1 <= n <= len(chunks)})
        if q.get("expect_in_answer"):
            text = " ".join(x.get("metin", "") for x in ans.get("cevap") or []) + " " + (ans.get("sesli_metin") or "")
            row["deger_dogru"] = (variants_in(q["varyantlar"], [x.get("metin", "") for x in ans.get("cevap") or []])
                                  if q.get("varyantlar") else all(value_in(s_, text) for s_ in q["expect_in_answer"]))
    if q.get("expect_clarify"):
        cls = json.loads(CLARIFY_CLASSES.read_text(encoding="utf-8")).get(q["qid"], {}).get("sinif")
        docs = [chunks[n - 1]["doc_id"] for n in v.get("secenekler") or [] if 1 <= n <= len(chunks)]
        verdict = options_verdict(list(dict.fromkeys(docs)), q.get("expect_docs") or []) if tur == "netlestirme" else None
        both = set(q.get("expect_docs") or []) <= set(row.get("atif_dokumanlari") or [])
        row.update(netlestirme_sinifi=cls, secenek_dokumanlari=docs, secenek_degerlendirme=verdict,
                   netlestirme_dogru=(verdict == "dogru") or (cls == "deger_ayni" and tur == "cevap" and both
                                                               and v["status"] in ("verified", "partial")))
    return row


def rescore_c(tag: str) -> list[str]:
    """Şema C turlarını (sema c/c150/c150b) bugünkü bench.schema_c doğrulamasıyla kayıttan yeniden puanlar (model çağrısı
    yok). Kayıtta akış zaman çizelgesi yok: ilk doğrulanmış cümle yaklaşık (ilk token ile toplam süre arasında karakter
    konumuna göre doğrusal), satırda 'ilk_cumle_yaklasik'."""
    global SCHEMA
    from pilot import pipeline
    from bench.schema_c import QUOTE_LIMIT, item_end_offsets, parse_c, to_legacy, verify_c
    install_search_cache(frozen=True)
    qs = {q["qid"]: q for q in questions(include_clarify=True)}
    done = []
    for f in sorted(RAW_DIR.glob(f"{tag}_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        sch = d.get("sema", "c")
        if not sch.startswith("c"):
            continue
        n_changed = 0
        for qid, row in d["rows"].items():
            if qid not in qs or not row.get("ham") or str(row.get("cikis", "")).startswith("kural:"):
                continue
            ans, status = parse_c(row["ham"], row.get("finish"))
            was_error = row.get("cikis") == "json_hata"
            if ans is None or status != "ok" or (ans.get("tur") != "cevap" and not was_error):
                continue
            pipeline.chat_json = lambda _u, a=ans: (to_legacy(a), {"llm_seconds": 0.0})
            res = pipeline.soru_cevapla(qs[qid]["q"])
            chunks = [h.chunk for h in res.hits]
            sources = {no: c["text"] for no, c in enumerate(chunks, start=1)}
            generated = {no: c.get("generated", "") for no, c in enumerate(chunks, start=1)}
            v = verify_c(ans, sources, generated, QUOTE_LIMIT.get(sch, 300))
            old = row.get("durum")
            if was_error:     # ayrıştırma değişti (strict=False, 2026-11-06): satır judge_c ile baştan
                SCHEMA = sch
                row.update(judge_c(qs[qid], res, {"c": ans}), json="ok", json_yeniden="strict=False")
                if ans.get("tur") != "cevap":
                    n_changed += 1
                    continue
            first = None
            ends = item_end_offsets(row["ham"])
            if row.get("akis_zaman"):     # gerçek akış zaman çizelgesi kayıtlıysa (2026-11-06 sonrası koşular)
                from bench.schema_c import first_verified_time
                first = first_verified_time(row["ham"], row["akis_zaman"], v["items"])
            elif row.get("ilk_token") and row.get("toplam") and row["ham"]:
                for end, it in zip(ends, v["items"]):
                    if it["ok"]:
                        first = row["ilk_token"] + (end / len(row["ham"])) * (row["toplam"] - row["ilk_token"])
                        break
            row.update(durum=v["status"], sorunlar=v["problems"][:4], ogeler=[i["ok"] for i in v["items"]],
                       ilk_dogrulanmis_cumle=first, ilk_cumle_yaklasik=not row.get("akis_zaman"))
            n_changed += old != v["status"]
        d["yeniden_puanlama_c"] = {"tarih": datetime.now().isoformat(timespec="seconds"), "rozeti_degisen": n_changed}
        f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        done.append(f"{f.name}: rozeti değişen {n_changed}")
    return done


def judge(q: dict[str, Any], res: Any) -> dict[str, Any]:
    """Soru sonucu: çıkış, arama isabeti, kaynağa dayanma, kaynak sayfa doğruluğu, beklenen değer."""
    a, st = res.answer, res.verification.status
    chunks = [h.chunk for h in res.hits]
    row: dict[str, Any] = {"durum": st, "sorunlar": res.verification.problems[:4],
                           "kontroller": res.verification.checks, "cevap": (a.get("cevap") or "")[:600],
                           "kaynaklar": [[c["doc_id"], c["pages"]] for c in chunks],
                           "sira": first_rank(chunks, q) if (q.get("expect_docs") or q.get("kabul")) else None}
    if not res.llm_called:
        row["cikis"] = "kural:" + rule_exit(res)
        if q.get("expect_clarify"):       # kural katmanının netleştirmesi de sistemin davranışı: aynı ölçüt
            from bench.doc_rules_diff import options_verdict
            cls = json.loads(CLARIFY_CLASSES.read_text(encoding="utf-8")).get(q["qid"], {}).get("sinif")
            docs = [o["doc_id"] for o in a.get("secenekler") or [] if "doc_id" in o] if st == "clarify" else []
            verdict = options_verdict(docs, q.get("expect_docs") or []) if st == "clarify" else None
            row.update(netlestirme_sinifi=cls, secenek_dokumanlari=docs, secenek_degerlendirme=verdict,
                       netlestirme_dogru=verdict == "dogru")
        return row
    if st == "clarify":
        row["cikis"] = "netlestirme"
    elif a.get("bulunamadi"):
        row["cikis"] = "bulunamadi"
    elif st == "failed" and not (a.get("cevap") or "").strip() and any("JSON" in p for p in res.verification.problems):
        row["cikis"] = "json_hata"
    else:
        row["cikis"] = "cevap"
    cited = [x.get("kaynak_no") for x in a.get("alintilar") or [] if isinstance(x, dict)]
    ok = [is_match(chunks[n - 1], q) for n in cited if isinstance(n, int) and 1 <= n <= len(chunks)]
    row["atif_dogru_biri"] = any(ok) if ok else None
    row["atif_dogru_hepsi"] = all(ok) if ok else None
    if q.get("expect_clarify"):       # bugünkü şemada netleştirme (judge_c ile aynı kurallar)
        from bench.clarify_model import option_docs
        from bench.doc_rules_diff import options_verdict
        cls = json.loads(CLARIFY_CLASSES.read_text(encoding="utf-8")).get(q["qid"], {}).get("sinif")
        docs = option_docs(res, res.hits) if st == "clarify" else []
        verdict = options_verdict(docs, q.get("expect_docs") or []) if st == "clarify" else None
        cited_docs = sorted({chunks[n - 1]["doc_id"] for n in cited if isinstance(n, int) and 1 <= n <= len(chunks)})
        both = set(q.get("expect_docs") or []) <= set(cited_docs)
        row.update(netlestirme_sinifi=cls, secenek_dokumanlari=docs, secenek_degerlendirme=verdict,
                   atif_dokumanlari=cited_docs, atlanan_netlestirme=a.get("atlanan_netlestirme"),
                   netlestirme_dogru=(verdict == "dogru") or (cls == "deger_ayni" and row["cikis"] == "cevap" and both
                                                               and st in ("verified", "partial")))
    if q.get("expect_in_answer"):
        text = ((a.get("cevap") or "") + " " + res.speech_text).casefold()
        # belge içi varyant (2026-11-06): değerler kendi varyant etiketiyle aynı yan cümlede
        row["deger_dogru"] = (variants_in(q["varyantlar"], a.get("cevap") or "") if q.get("varyantlar")
                              else all(value_in(s, text) for s in q["expect_in_answer"]))
    return row


# ---------- kayıttan yeniden puanlama (model çağrısı yok) ----------

QUOTE_RE = re.compile(r'"metin"\s*:\s*"((?:[^"\\]|\\.)*)"')
HARD_CHECKS = ("alinti_var", "alinti_birebir", "sayilar_alintida", "tolerans_tam", "cevap_var", "tekrar_yok",
               "alfabe_dogru")


def status_from(checks: dict[str, Any]) -> str:
    """verify.py ve pipeline'ın varyant kuralıyla aynı karar (kesik kayıtlar için)."""
    if any(checks.get(k) is False for k in HARD_CHECKS):
        return "failed"
    ok = checks.get("atif_gecerli") and checks.get("alinti_kaynak_metni", True) and checks.get("varyant_belirli", True)
    return "verified" if ok else "partial"


def rescore(tag: str, force: bool = False) -> list[str]:
    """<tag>_*.json kayıtlarını bugünkü verify.py ile yeniden puanlar; kayıtlı model çıktısı aynı arama önbelleğiyle
    pipeline'dan geçer. Eski puan satırda 'onceki_puan'da kalır. Ham çıktısı kesik kaydedilmiş satırlarda (2026-11-05
    "ana" turu, 1500 karakter) cevap ayrıştırılamaz: kaynaklar yine pipeline'dan, alıntılar kesik metinden, cevap
    kayıttaki ilk 600 karakterden; koşu anında kalan sayı ve atıf kontrolleri yeniden, diğerleri kayıttan (yaklaşık,
    'kesik_kayit')."""
    from pilot import pipeline
    from pilot.verify import cites_in, numbers_in, word_numbers
    install_search_cache(frozen=True)
    qs = {q["qid"]: q for q in questions()}
    orig, cur, done = pipeline.verify, {}, []

    def cap(answer: dict, sources: dict, generated: dict | None = None) -> Any:
        cur["sources"] = sources
        return orig(answer, sources, generated)

    pipeline.verify = cap
    try:
        for f in sorted(RAW_DIR.glob(f"{tag}_*.json")):
            d = json.loads(f.read_text(encoding="utf-8"))
            if (not force and d.get("verify") == VERIFY_TAG and d.get("deger") == VALUE_TAG) or not isinstance(d.get("rows"), dict):
                continue
            n_cut = n_changed = n_value = 0
            for qid, row in d["rows"].items():
                if row.get("cikis") != "cevap" or qid not in qs:
                    continue
                keep = ("durum", "sorunlar", "kontroller", "atif_dogru_biri", "atif_dogru_hepsi", "deger_dogru")
                old = {k: row[k] for k in keep if k in row}
                ans = parse_answer(row.get("ham", ""), row.get("finish"))[0]
                if qs[qid].get("onceki_soru"):
                    # Soru metni sonradan yeniden yazıldı: kayıtlı cevap eski soruya ait, arama önbelleği yeni soruyu
                    # bilmiyor. Rozet kayıttan kalır; beklenen değer kayıttaki cevaptan (bilgi), satır işaretlenir.
                    row["soru_degisti"] = True
                    if qs[qid].get("expect_in_answer"):
                        row["deger_dogru"] = all(value_in(s_, row.get("cevap", "")) for s_ in qs[qid]["expect_in_answer"])
                elif ans is not None:
                    pipeline.chat_json = lambda _u, a=ans: (dict(a), {"llm_seconds": 0.0})
                    new = judge(qs[qid], pipeline.soru_cevapla(qs[qid]["q"]))
                    row.update({k: new[k] for k in keep if k in new})
                else:
                    n_cut += 1
                    dummy = {"alintilar": [], "cevap": "-", "sesli_metin": "", "bulunamadi": False}
                    pipeline.chat_json = lambda _u, a=dummy: (dict(a), {"llm_seconds": 0.0})
                    cur.clear()
                    pipeline.soru_cevapla(qs[qid]["q"])
                    quote = " ".join(json.loads(f'"{m}"') for m in QUOTE_RE.findall(row.get("ham", "")))
                    checks = dict(row.get("kontroller") or {})
                    text = row.get("cevap", "")
                    # A+B yalnız gevşetir: koşu anında tam metinle geçen kontrol geçer kalır; yalnız kalanlar yeniden.
                    cites = cites_in(text)
                    checks["sayilar_alintida"] = bool(checks.get("sayilar_alintida")) or not (
                        numbers_in(text) - numbers_in(quote) - word_numbers(quote))
                    checks["atif_gecerli"] = bool(checks.get("atif_gecerli")) or (
                        bool(cites) and cites <= set(cur.get("sources") or {}))
                    row.update(durum=status_from(checks), kontroller=checks, kesik_kayit=True)
                    if qs[qid].get("expect_in_answer"):      # kesik kayıt: cevabın kayıttaki ilk 600 karakteri
                        row["deger_dogru"] = all(value_in(s, text) for s in qs[qid]["expect_in_answer"])
                n_changed += row["durum"] != old.get("durum")
                n_value += row.get("deger_dogru") != old.get("deger_dogru")
                row.setdefault("onceki_puan", old)        # ilk yeniden puanlamadan önceki puan korunur
            d["verify"], d["deger"] = VERIFY_TAG, VALUE_TAG
            d["yeniden_puanlama"] = {"tarih": datetime.now().isoformat(timespec="seconds"), "kesik_kayit": n_cut,
                                     "rozeti_degisen": n_changed, "degeri_degisen": n_value}
            f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
            done.append(f"{f.name}: rozeti değişen {n_changed}, beklenen değeri değişen {n_value}, kesik kayıt {n_cut}")
    finally:
        pipeline.verify = orig
    return done


# ---------- rapor ----------

def report_c(tag: str) -> str:
    """Şema C turu (nihai tur): tur dağılımı, rozet, beklenen değer, "bulunamadı", netleştirme (değer farklı/aynı),
    ilk token ve ilk doğrulanmış cümle. Kalite yalnız cevap gelen sorularda; onaysız sorular ayrı tutulmaz (set onaylı)."""
    qs = {q["qid"]: q for q in questions(include_clarify=True)}
    runs = {f.stem[len(tag) + 1:]: json.loads(f.read_text(encoding="utf-8")) for f in sorted(RAW_DIR.glob(f"{tag}_*.json"))}
    pct_ = lambda a, b: f"{a}/{b} ({a / b:.0%})" if b else "–"
    s_ = lambda x: "–" if x is None or x != x else (f"{x * 1000:.0f} ms" if x < 1 else f"{x:.2f} sn".replace(".", ","))
    L = [f"# Adım 2 nihai tur, şema C: `{tag}`", "", "Şema C (plan §15.0): her cümle kendi alıntısıyla; tur = cevap | "
         "netlestirme | bulunamadi. Rozet öğe başına doğrulamadan (`bench/schema_c.py`). Pipeline'ın varyant kuralı C'de "
         "uygulanmadı.", "",
         "| Model | çağrı | JSON/şema hatası | doğru \"bulunamadı\" (model) | doğrulanmış görünen yanlış | cevaplı: ✓ / ⚠ / ✖ | "
         "beklenen değer | netleştirme, değer farklı | netleştirme, değer aynı | gereksiz netleştirme | ilk token p50 / p95 | "
         "ilk doğrulanmış cümle p50 / p95 | maliyet |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in runs.items():
        R = r["rows"]
        model = {q: x for q, x in R.items() if not str(x.get("cikis", "")).startswith("kural:") and x.get("cikis") != "cevapsiz"}
        nf = [q for q in model if qs.get(q, {}).get("expect_not_found")]
        cl = [q for q in model if qs.get(q, {}).get("expect_clarify")]
        an = [q for q in model if q not in nf and q not in cl]
        st = Counter(R[q]["durum"] for q in an if R[q].get("cikis") == "cevap")
        dv = [R[q]["deger_dogru"] for q in an if "deger_dogru" in R[q]]
        bad = sum(R[q].get("cikis") == "cevap" and R[q].get("durum") in ("verified", "partial") for q in nf)
        allcl = [q for q in R if qs.get(q, {}).get("expect_clarify") and R[q].get("cikis") != "cevapsiz"]   # kural dahil
        fark = [q for q in allcl if R[q].get("netlestirme_sinifi") == "deger_farkli"]
        ayni = [q for q in allcl if R[q].get("netlestirme_sinifi") == "deger_ayni"]
        ft = [R[q]["ilk_token"] for q in model if R[q].get("ilk_token")]
        fv = [R[q]["ilk_dogrulanmis_cumle"] for q in an if R[q].get("ilk_dogrulanmis_cumle")]
        js = sum(R[q].get("json") not in (None, "ok") for q in R)
        classes = json.loads(CLARIFY_CLASSES.read_text(encoding="utf-8"))
        var = [q for q in model if classes.get(q, {}).get("sinif") == "belge_ici_varyant"]
        var_ok = sum(R[q].get("cikis") == "netlestirme"
                     or variants_in(qs[q].get("varyantlar") or [], R[q].get("cevap", "")) for q in var)
        unnec = sum(R[q].get("cikis") == "netlestirme" for q in an + nf if q not in var)
        L.append(f"| {k} | {len(model)} | {js} | {pct_(sum(R[q]['cikis'] == 'bulunamadi' for q in nf), len(nf))} | **{bad}** | "
                 f"{st['verified']} / {st['partial']} / {st['failed']} | {pct_(sum(dv), len(dv))} | "
                 f"{pct_(sum(bool(R[q].get('netlestirme_dogru')) for q in fark), len(fark))} | "
                 f"{pct_(sum(bool(R[q].get('netlestirme_dogru')) for q in ayni), len(ayni))} | "
                 f"{unnec} (belge içi varyant doğru {var_ok}/{len(var)}) | {s_(percentile(ft, .5))} / {s_(percentile(ft, .95))} | "
                 f"{s_(percentile(fv, .5))} / {s_(percentile(fv, .95))} | {r.get('cost_usd', 0):.4f} USD |")
    L += ["", "İlk doğrulanmış cümle: model isteğinden, akışta ilk geçen öğenin tamamlandığı ana (model tarafı; uçtan uca "
          "süre ayrıca, arama öncesi dahil). Değer aynı: netleştirme ya da iki ürünün kaynağını birlikte gösteren doğrulanmış "
          "cevap doğru sayılır.", ""]
    L += indent_table(tag)
    return "\n".join(L)


def is_indented(raw: str) -> bool:
    """Model JSON'u girintili (satır sonu + boşluklu) mı yazmış (2026-11-06: Venice davranış değişikliği)."""
    return bool(re.match(r"\s*\{\s*\n", raw or ""))


def indent_table(tag: str | None = None) -> list[str]:
    """Girintili JSON oranı, sağlayıcı ve koşu bazında (bütün nihai_* Gemma 4 koşuları; tag'in koşuları kalın).
    Girinti token, toplam süre ve kesik demek; ilk doğrulanmış cümle ve kesik sayısı aynı satırda."""
    L = ["## Girintili JSON (sağlayıcı ve koşu bazında)", "",
         "Aynı istek ve şemada sağlayıcının JSON'u girintili yazıp yazmadığı. Girinti çıktı tokeni ve kesik demek.", "",
         "| Koşu | başlangıç | sağlayıcı | şema | girintili / çıktılı | çıktı tokeni p50 (cevap) | kesik (finish=length) | "
         "ilk doğrulanmış cümle p50 / p95 |", "|---|---|---|---|---|---|---|---|"]
    s_ = lambda x: "–" if x is None or x != x else (f"{x * 1000:.0f} ms" if x < 1 else f"{x:.2f} sn".replace(".", ","))
    for f in sorted(RAW_DIR.glob("nihai_*.json"), key=lambda p: json.loads(p.read_text(encoding="utf-8")).get("start", "")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if "gemma-4-26b" not in (d.get("spec") or {}).get("id", ""):
            continue
        R = d["rows"]
        out = [x for x in R.values() if x.get("ham")]
        ind = sum(is_indented(x["ham"]) for x in out)
        tok = [x["cikis_token"] for x in out if x.get("cikis") == "cevap" and x.get("cikis_token")]
        fv = [x["ilk_dogrulanmis_cumle"] for x in R.values() if x.get("ilk_dogrulanmis_cumle")]
        name = f.stem if not tag or not f.stem.startswith(tag + "_") else f"**{f.stem}**"
        L.append(f"| {name} | {d.get('start', '')[:16].replace('T', ' ')} | {d['spec'].get('provider')} | {d.get('sema')} | "
                 f"{ind}/{len(out)} ({ind / max(len(out), 1):.0%}) | {percentile(tok, .5):.0f} | "
                 f"{sum(x.get('finish') == 'length' for x in out)} | {s_(percentile(fv, .5))} / {s_(percentile(fv, .95))} |")
    return L + [""]


def report(tag: str, latency_tag: str | None) -> str:
    qs = {q["qid"]: q for q in questions()}
    rules = json.loads((RAW_DIR / "kural_cikislari.json").read_text(encoding="utf-8"))
    runs = {f.stem.split("_", 1)[1]: json.loads(f.read_text(encoding="utf-8"))
            for f in sorted(RAW_DIR.glob(f"{tag}_*.json"))}
    lat = ({f.stem.split("_", 1)[1]: json.loads(f.read_text(encoding="utf-8"))
            for f in sorted(RAW_DIR.glob(f"{latency_tag}_*.json"))} if latency_tag else {})
    order = [k for k in MODELS if k in runs]
    nf = [k for k, q in qs.items() if q.get("expect_not_found")]
    ans = [k for k, q in qs.items() if not q.get("expect_not_found")]
    approved = lambda k: qs[k].get("dogrulandi") is not False
    pct_ = lambda a, b: f"{a}/{b} ({a / b:.0%})".replace(".", ",") if b else "–"
    s = lambda x: "–" if x is None or x != x else (f"{x * 1000:.0f} ms" if x < 1 else f"{x:.2f} sn".replace(".", ","))
    nf_un = sum(not approved(k) for k in nf)
    nf_model = [k for k in nf if rules.get(k) not in ("yabanci_marka", "kod_yok")]
    L = ["# Adım 2: cevap modeli seçimi, ilk tur (ön eleme)", "",
         f"> **\"Bulunamadı\" kararının {nf_un} sorusu onaysız** (A114–A130; {len(nf)} sorunun {nf_un}'si; "
         f"kural çıkışları hariç modelin karar verdiği {len(nf_model)} sorunun "
         f"{sum(not approved(k) for k in nf_model)}'i). **Bu koşu ön elemedir; nihai seçim onaylı ve büyütülmüş sette "
         f"yapılacak.** Cevaplı sorularda da {sum(not approved(k) for k in ans)}/{len(ans)} onaysız. Süreler geliştirme "
         "makinesinin bağlantısından; üretimi temsil etmez.", "",
         "Arama sabit: uygulamanın varsayılan yolu (bge-m3 + BM25, rerank kapalı, ilke dışı kurallar kapalı), "
         "`manuals` koleksiyonu; bütün modeller aynı kaynakları gördü. Aynı sistem talimatı ve şema, temperature 0, "
         "düşünme kapalı; modele özel istem ayarı yok. Yeniden deneme bütün modellerde aynı: ilk token gelmeden "
         f"429/5xx/bağlantı hatasında {RETRY_WAIT:.0f} sn sonra bir kez; yine olmazsa soru cevapsız (kalite "
         "metriklerine girmez). Plan: [plan_cevap_modeli_2026-11-05.md](plan_cevap_modeli_2026-11-05.md).", ""]
    rescored = {k: r["yeniden_puanlama"] for k, r in runs.items() if r.get("yeniden_puanlama")}
    L += [f"**Rozetler `verify.py` {VERIFY_TAG} ile.** Rozet davranışı değişti: çoklu atıf (`[1, 2]`) atıf sayılıyor ve "
          "içindeki rakamlar değer sayılmıyor; atıftan sonra, `<br>` sonrası ve Markdown kalın madde numaraları liste "
          "numarası; `2.00` = `2`, `.5` = `0.5`; alıntıda yazıyla geçen 1–12 (`six months`) alıntı sayısı. Birim "
          "dönüşümü, türetilmiş sayı ve alıntıda olmayan değer yine ✖. Gerekçe ve önce/sonra: "
          "[okuma_sayi_uzunluk_2026-11-05.md](okuma_sayi_uzunluk_2026-11-05.md)."
          + (" Önceki sürümle koşulan kayıtlar model çağrısı olmadan yeniden puanlandı (`--rescore`): "
             + ", ".join(f"{k} rozeti değişen {v['rozeti_degisen']}, kesik kayıt {v['kesik_kayit']}"
                         for k, v in rescored.items())
             + ". Kesik kayıt: ham çıktı 1500 karakterde kesik kaydedilmiş, rozeti yaklaşık (sayı ve atıf kontrolleri "
               "kayıttaki cevabın ilk 600 karakterinden); tablolarda ayrı sütunda." if rescored else ""), ""]
    rc = Counter(v for v in rules.values() if v)
    L += [f"**Kural çıkışları (modelden bağımsız, bir kez):** {dict(rc)}; \"bulunamadı\" beklenen 21 sorudan "
          f"{sum(1 for k in nf if rules.get(k) in ('yabanci_marka', 'kod_yok'))} kuralla çıkıyor.", ""]

    L += ["## Dayanıklılık", "", "| Model | Sağlayıcı (sabit) | ZDR sağlayıcı sayısı | çağrı | 429 | diğer hata | "
          "yeniden deneme | cevapsız kalan | başka sağlayıcıdan gelen | düşünme kontrolü |", "|---|---|---|---|---|---|---|---|---|---|"]
    for k in order:
        r = runs[k]
        rows = [x for x in r["rows"].values() if x.get("denemeler")]
        att = [a for x in rows for a in x["denemeler"]]
        e429 = sum(a["err"].startswith("429") for a in att)
        other = sum(bool(a["err"]) and not a["err"].startswith("429") for a in att)
        retried = sum(len(x["denemeler"]) > 1 for x in rows)
        unans = sum(x.get("cikis") == "cevapsiz" for x in r["rows"].values())
        prov = MODELS[k]["provider"]
        foreign = sum(1 for x in rows if x.get("provider") and x["provider"].lower().replace(" ", "") not in
                      (prov, "yerel") and not x["provider"].lower().startswith(prov))
        chk = r.get("dusunme_kontrolu")
        L.append(f"| {k} (`{MODELS[k]['id']}`) | {prov} | {len(r['zdr_providers']) if not MODELS[k].get('local') else '–'} | "
                 f"{len(att)} | {e429} | {other} | {retried} | {unans} | {foreign} | "
                 f"{'tamam' if not chk else ('tamam' if chk['ok'] else 'KAPANMADI')} |")

    L += ["", "## \"Bulunamadı\" (21 soru: 4 onaylı + 17 onaysız)", "",
          "| Model | doğru \"bulunamadı\", toplam | … modelin karar verdiği soruda | netleştirme | cevap üretti | "
          "… doğrulanmış görünen yanlış (✓/⚠) | … kesik kayıt (yaklaşık) | JSON hatası | cevapsız (kaliteden ayrı) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for k in order:
        R = runs[k]["rows"]
        got = [q for q in nf if q in R and R[q]["cikis"] != "cevapsiz"]
        model_q = [q for q in got if not R[q]["cikis"].startswith("kural:")]
        ok_rule = sum(R[q]["cikis"].startswith("kural:") for q in got)
        ok_model = sum(R[q]["cikis"] == "bulunamadi" for q in model_q)
        made = [q for q in model_q if R[q]["cikis"] == "cevap"]
        bad = sum(R[q]["durum"] in ("verified", "partial") for q in made)
        L.append(f"| {k} | {pct_(ok_rule + ok_model, len(got))} | {pct_(ok_model, len(model_q))} | "
                 f"{sum(R[q]['cikis'] == 'netlestirme' for q in model_q)} | {len(made)} | **{bad}** | "
                 f"{sum(bool(R[q].get('kesik_kayit')) for q in made)} | "
                 f"{sum(R[q]['cikis'] == 'json_hata' for q in model_q)} | {sum(R[q]['cikis'] == 'cevapsiz' for q in nf if q in R)} |")
    L += ["", "Taban (2026-10-27, yerel qwen2.5:7b, aynı 21 soru, o günkü arama): doğru \"bulunamadı\" %48, doğrulanmış "
          "görünen yanlış 3.", ""]

    L += ["## Cevaplı sorular (kalite, cevap gelen sorularda)", "",
          "| Model | Set | soru | yanlış ret | … kaynak ilk 5'teydi (model hatası) | … arama getirmedi | netleştirme | "
          "✓ / ⚠ / ✖ | … kesik kayıt (yaklaşık) | beklenen değer cevapta | atıf: en az biri doğru sayfa | "
          "atıf: hepsi doğru | JSON hatası |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k in order:
        R = runs[k]["rows"]
        ocr = lambda q: "ocr" in (qs[q].get("zorluk") or [])
        for label, sel in (("onaylı", lambda q: approved(q)), ("… onaylı, OCR soruları", lambda q: approved(q) and ocr(q)),
                           ("onaysız", lambda q: not approved(q))):
            qq = [q for q in ans if q in R and sel(q) and R[q]["cikis"] not in ("cevapsiz",) and not R[q].get("soru_degisti")
                  and not R[q]["cikis"].startswith("kural:")]
            if not qq:
                continue
            ref = [q for q in qq if R[q]["cikis"] == "bulunamadi"]
            ref_in = sum(R[q]["sira"] is not None and R[q]["sira"] <= 5 for q in ref)
            made = [q for q in qq if R[q]["cikis"] == "cevap"]
            st = Counter(R[q]["durum"] for q in made)
            dv = [R[q]["deger_dogru"] for q in made if "deger_dogru" in R[q]]
            a1 = [R[q]["atif_dogru_biri"] for q in made if R[q].get("atif_dogru_biri") is not None]
            a2 = [R[q]["atif_dogru_hepsi"] for q in made if R[q].get("atif_dogru_hepsi") is not None]
            L.append(f"| {k} | {label} | {len(qq)} | {pct_(len(ref), len(qq))} | {ref_in} | {len(ref) - ref_in} | "
                     f"{sum(R[q]['cikis'] == 'netlestirme' for q in qq)} | {st['verified']} / {st['partial']} / "
                     f"{st['failed']} | {sum(bool(R[q].get('kesik_kayit')) for q in made)} | "
                     f"{pct_(sum(dv), len(dv))} | {pct_(sum(a1), len(a1))} | {pct_(sum(a2), len(a2))} | "
                     f"{sum(R[q]['cikis'] == 'json_hata' for q in qq)} |")
    L += ["", "Soru metni sonradan yeniden yazılan sorular (A008, 2026-11-05) bu turun kalite tablolarında yok: kayıtlı cevap eski soruya ait. "
          "Atıf doğruluğu: cevabın alıntı yaptığı kaynak numaralarının parçaları beklenen doküman ve sayfayla "
          "(`is_match`) eşleşiyor mu; alıntısız cevap paydada yok.", "",
          "**Rozet nedenleri** (cevaplı sorularda üretilen cevaplar; `verify.py` kontrolleri, bir cevapta birden çok olabilir):", "",
          "| Model | ✖: alıntıda olmayan sayı | ✖: alıntı birebir değil | ✖ / ⚠: geçerli [n] atfı yok | "
          "⚠: değer varyanta göre değişiyor | ⚠: alıntı şekil açıklamasından |", "|---|---|---|---|---|---|"]
    for k in order:
        made = [r for q, r in runs[k]["rows"].items() if q in ans and r.get("cikis") == "cevap"]
        bad = lambda key: sum((r.get("kontroller") or {}).get(key) is False for r in made)
        L.append(f"| {k} | {bad('sayilar_alintida')} | {bad('alinti_birebir')} | {bad('atif_gecerli')} | "
                 f"{bad('varyant_belirli')} | {bad('alinti_kaynak_metni')} |")
    L.append("")

    L += ["## JSON (ayrı metrik, modele giden bütün çağrılar)", "", "| Model | çağrı | ok | şema dışı | boş | yarıda kesik | "
          "ayrıştırılamadı | düşünce bloğu / öntext atıldı |", "|---|---|---|---|---|---|---|---|"]
    for k in order:
        js = Counter(x.get("json") for x in runs[k]["rows"].values() if x.get("json"))
        th = sum(bool(x.get("dusunce_blogu")) for x in runs[k]["rows"].values())
        L.append(f"| {k} | {sum(js.values())} | {js['ok']} | {js['sema_disi']} | {js['bos']} | {js['kesik']} | "
                 f"{js['gecersiz']} | {th} |")

    L += ["", "## İlk token ve süre (§9.3 eşikleri: 1,2 sn hedge, 1,5 sn yedek sağlayıcı, 20 sn toplam)", "",
          "| Model | Tur | n | ilk token p50 | p95 | ≤ 1,2 sn | ≤ 1,5 sn | toplam p50 | p95 | > 20 sn | sağlayıcı |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k in order:
        for tur, src in (("ana", runs.get(k)), ("ikinci", lat.get(k))):
            if not src:
                continue
            rows = [x for x in src["rows"].values() if x.get("ilk_token") is not None]
            ft, tt = [x["ilk_token"] for x in rows], [x["toplam"] for x in rows]
            prov = Counter(x.get("provider") for x in rows)
            L.append(f"| {k} | {tur} ({src.get('start', '')[11:16]}) | {len(rows)} | {s(percentile(ft, .5))} | "
                     f"{s(percentile(ft, .95))} | {pct_(sum(x <= 1.2 for x in ft), len(ft))} | "
                     f"{pct_(sum(x <= 1.5 for x in ft), len(ft))} | {s(percentile(tt, .5))} | {s(percentile(tt, .95))} | "
                     f"{sum(x > 20 for x in tt)} | {dict(prov)} |")
    L += ["", "qwen2.5:7b yerelde (dizüstü CPU): süreleri bulutla karşılaştırılamaz.", "",
          "## Maliyet", "", "| Model | Tur | USD | soru başına |", "|---|---|---|---|"]
    tot = 0.0
    for k in order:
        for tur, src in (("ana", runs.get(k)), ("ikinci", lat.get(k))):
            if src:
                tot += src["cost_usd"]
                n = max(1, len(src["rows"]))
                L.append(f"| {k} | {tur} | {src['cost_usd']:.4f} | {src['cost_usd'] / n:.5f} |")
    L += ["", f"Bu rapordaki koşular: {tot:.4f} USD. Adım 2 turunun toplam harcaması (geçersiz sayılan koşular "
          f"dahil, `ham/` altındaki bütün dosyalar): {spent_all():.4f} USD (sınır 1,5 USD).", ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--models", nargs="*", default=[])
    ap.add_argument("--tag", default="ana")
    ap.add_argument("--n", type=int, default=0, help="0: bütün sorular; >0: cevaplı sorulardan örneklem (süre turu)")
    ap.add_argument("--seed", type=int, default=20261105)
    ap.add_argument("--max-usd", type=float, default=1.5, help="bütün turlar ve modeller toplamı")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--force", action="store_true", help="--rescore: aynı sürümle puanlanmış kayıtları da (etiket değişince)")
    ap.add_argument("--rescore", nargs="*", metavar="TAG",
                    help="kayıtları bugünkü verify.py ile yeniden puanla (model çağrısı yok); örn. --rescore ana bozuk1")
    ap.add_argument("--latency-tag", default="sure2")
    ap.add_argument("--rescore-c", nargs="*", metavar="TAG", help="şema C turlarını kayıttan yeniden puanla")
    ap.add_argument("--report-c", metavar="TAG", help="şema C turunun raporu (eval/bench/adim2/<TAG>_rapor_<tarih>.md)")
    ap.add_argument("--setler", nargs="+", help="soru setleri (varsayılan: bilinen setler + aday_sorular); "
                    "örn. --setler aday_sorular_ek (yeni onaylanan sorular; arama önbelleği --prepare ile)")
    ap.add_argument("--netlestirme", choices=["haric", "dahil", "yalniz"],
                    help="netleştirme beklenen 18 soru (varsayılan: C'de dahil, bugünkü şemada hariç)")
    ap.add_argument("--schema", choices=["bugun", "c", "c150", "c150b", "c150bT", "c150bJ"], default="bugun", help="cevap şeması (c: plan §15.0, yalnız ölçüm aracı)")
    ap.add_argument("--max-tokens", type=int, default=0, help="deneme: max_tokens (0: uygulamanın değeri)")
    ap.add_argument("--ids", nargs="+", default=[], help="deneme: yalnız bu soru kimlikleri")
    a = ap.parse_args()
    global SCHEMA, SETS, MAX_TOKENS, ONLY_IDS
    SCHEMA = a.schema
    MAX_TOKENS, ONLY_IDS = a.max_tokens, a.ids
    if a.setler:
        SETS = list(a.setler)
    if a.prepare:
        prepare()
    for t in a.rescore or []:
        print("\n".join(rescore(t, a.force)) or f"{t}: yeniden puanlanacak kayıt yok", flush=True)
    for k in a.models:
        path = run_model(k, a.tag, a.n, a.max_usd, a.seed, a.netlestirme)
        print(path, flush=True)
        if "bütçe" in json.loads(path.read_text(encoding="utf-8")).get("durdu", ""):
            break
    for t in a.rescore_c or []:
        for line in rescore_c(t):
            print(line, flush=True)
    if a.report_c:
        md = report_c(a.report_c)
        print(write_result(f"{a.report_c}_rapor", {"rapor": md}, md, out_dir=RAW_DIR.parent))
    if a.report:
        md = report("ana", a.latency_tag)
        print(write_result("adim2_cevap_modeli", {"rapor": md}, md, out_dir=RAW_DIR.parent))


if __name__ == "__main__":
    main()
