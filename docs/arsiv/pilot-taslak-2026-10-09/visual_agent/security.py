"""Kimlik doğrulama ve marka bazlı yetkilendirme.

İlkeler (06-veri-guvenligi-ve-erisim.md, 7.3):
- Yetki kararı LLM'e bırakılmaz. Yetkisiz parça LLM'e hiç ulaşmaz.
- Filtre sunucuda, aramadan ÖNCE, tek bir merkezi fonksiyonda (`access_filter`) üretilir.
- Arayüzdeki marka seçimi sadece daraltır, genişletemez.
- Varsayılan kapalı: Markası kullanıcıya atanmamış 'brand' erişimli doküman görünmez.
- Aynı kontrol tüm erişim noktalarında kullanılır: arama, sayfa görüntüleme (`can_view_document`).
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .config import CONFIG_DIR, DocMeta

USERS_FILE = CONFIG_DIR / "users.json"
_lock = threading.Lock()


@dataclass
class User:
    email: str
    name: str
    role: str = "user"
    brands: list[str] = field(default_factory=list)
    full_document: bool = False
    consent_at: str | None = None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _load() -> dict:
    return json.loads(USERS_FILE.read_text("utf-8"))


def _save(data: dict) -> None:
    with _lock:
        USERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


def _to_user(u: dict) -> User:
    return User(email=u["email"], name=u.get("name", u["email"]), role=u.get("role", "user"),
                brands=list(u.get("brands", [])), full_document=bool(u.get("full_document", False)),
                consent_at=u.get("consent_at"))


def authenticate(email: str, code: str) -> User | None:
    email = email.strip().lower()
    for u in _load()["users"]:
        if u["email"].lower() == email and u.get("code_sha256") == _hash(code.strip()):
            return _to_user(u)
    return None


def get_user(email: str) -> User | None:
    for u in _load()["users"]:
        if u["email"].lower() == email.lower():
            return _to_user(u)
    return None


def list_users() -> list[User]:
    return [_to_user(u) for u in _load()["users"]]


def upsert_user(user: User, code: str | None = None) -> None:
    data = _load()
    for u in data["users"]:
        if u["email"].lower() == user.email.lower():
            u.update({"name": user.name, "role": user.role, "brands": user.brands,
                      "full_document": user.full_document})
            if code:
                u["code_sha256"] = _hash(code)
            break
    else:
        if not code:
            raise ValueError("Yeni kullanıcı için erişim kodu gerekli")
        data["users"].append({"email": user.email.lower(), "name": user.name, "code_sha256": _hash(code),
                              "role": user.role, "brands": user.brands, "full_document": user.full_document,
                              "consent_at": None})
    _save(data)


def delete_user(email: str) -> None:
    data = _load()
    data["users"] = [u for u in data["users"] if u["email"].lower() != email.lower()]
    _save(data)


def record_consent(email: str) -> str:
    """Aydınlatma metninin okunup onaylandığı zamanı kaydeder (cevaplar.md: aydınlatma metni gerekli)."""
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data = _load()
    for u in data["users"]:
        if u["email"].lower() == email.lower():
            u["consent_at"] = ts
    _save(data)
    return ts


# ----------------------------------------------------------------------------- yetki

def allowed_brands(user: User, selected: list[str] | None = None) -> list[str]:
    """Kullanıcının görebileceği markalar. Seçim sadece daraltır."""
    if selected:
        return [b for b in selected if b in user.brands]
    return list(user.brands)


def access_filter(user: User, selected_brands: list[str] | None = None, include_public: bool = True,
                  extra_must: list | None = None):
    """Qdrant filtresi: (access=public) VEYA (brand ∈ izinli markalar), artı ek koşullar.

    Tek merkezi yetki noktası. Her aramada çağrılır.
    """
    from qdrant_client import models as qm
    brands = allowed_brands(user, selected_brands)
    should = []
    if brands:
        should.append(qm.FieldCondition(key="brand", match=qm.MatchAny(any=brands)))
    if include_public and not selected_brands:
        should.append(qm.FieldCondition(key="access", match=qm.MatchValue(value="public")))
    elif include_public and selected_brands:
        # Kullanıcı belirli marka seçtiyse, o markaların herkese açık dokümanları da görünür
        should.append(qm.Filter(must=[qm.FieldCondition(key="access", match=qm.MatchValue(value="public")),
                                      qm.FieldCondition(key="brand", match=qm.MatchAny(any=selected_brands))]))
    if not should:
        # Hiçbir şeye yetkisi yok: hiçbir sonuç dönmesin
        should.append(qm.FieldCondition(key="doc_id", match=qm.MatchValue(value="__yok__")))
    return qm.Filter(should=should, must=extra_must or [])


def can_view_document(user: User, meta: DocMeta) -> bool:
    return meta.access == "public" or meta.brand in user.brands


def view_pages(user: User, page: int, n_pages: int, window: int) -> list[int]:
    """Kullanıcıya gösterilecek sayfa aralığı (cevaplar.md: en fazla bir önce ve bir sonrası)."""
    if user.full_document:
        return list(range(1, n_pages + 1))
    return [p for p in range(page - window, page + window + 1) if 1 <= p <= n_pages]
