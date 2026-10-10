"""Lokal LLM (Ollama) çağrısı. Sağlayıcı değişirse yalnızca bu dosya değişir."""
import json
from typing import Any

import ollama

from .config import LLM_MODEL, LLM_NUM_CTX, LLM_NUM_PREDICT
from .prompts import ANSWER_SCHEMA, SYSTEM_PROMPT


def chat_json(user_content: str) -> tuple[dict[str, Any], dict[str, float]]:
    """Şemaya uyan JSON cevap ve süre/token bilgisi."""
    resp = ollama.chat(
        model=LLM_MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_content}],
        format=ANSWER_SCHEMA,
        options={"temperature": 0, "num_ctx": LLM_NUM_CTX, "num_predict": LLM_NUM_PREDICT},
        keep_alive="30m",
    )
    stats = {"prompt_tokens": resp.get("prompt_eval_count", 0), "output_tokens": resp.get("eval_count", 0),
             "llm_seconds": resp.get("total_duration", 0) / 1e9}
    return json.loads(resp["message"]["content"]), stats
