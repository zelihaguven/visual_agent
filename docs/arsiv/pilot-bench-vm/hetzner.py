"""Aşama 3 VM'i: Hetzner Cloud API ile aç, durumunu gör, sil. Gerçek maliyet: saat × API fiyatı + OpenRouter anahtar kullanımı.

Kullanım (yerelde, Pilot klasöründe; HCLOUD_TOKEN ortam değişkeni, ayrı proje önerilir):
    python -m bench.vm.hetzner price                       # ccx43 saatlik fiyatı (API'nin pricing ucu)
    python -m bench.vm.hetzner create [--location nbg1]    # SSH anahtarı + sunucu; IP'yi yazar
    python -m bench.vm.hetzner status
    python -m bench.vm.hetzner delete                      # sunucu + SSH anahtarı; silindiğini doğrular
    python -m bench.vm.hetzner cost [--openrouter-env OPENROUTER_API_KEY_VM]

- Sunucu "visual-agent-asama3" etiketiyle açılır; durdurulmuş sunucu da faturalanır, bu yüzden iş bitince delete.
- SSH anahtarı yerelde ~/.ssh/visual_agent_asama3 (ed25519, parolasız, yalnız bu iş); public kısmı Hetzner'e yüklenir.
- Belirteçler yalnız ortamdan okunur, hiçbir yere yazılmaz; bu betik kayıt dosyasına yalnız sunucu kimliği/IP/saat yazar.
"""
import argparse
import json
import math
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

API = "https://api.hetzner.cloud/v1"
NAME = "visual-agent-asama3"
TYPE = "ccx43"
IMAGE = "ubuntu-24.04"
KEY_PATH = Path.home() / ".ssh" / "visual_agent_asama3"
STATE = Path(__file__).resolve().parents[2] / "data" / "scale" / "vm_state.json"


def _token() -> str:
    t = os.environ.get("HCLOUD_TOKEN")
    if not t and os.name == "nt":
        import winreg
        try:
            t = winreg.QueryValueEx(winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment"), "HCLOUD_TOKEN")[0]
        except OSError:
            t = None
    if not t:
        raise SystemExit("HCLOUD_TOKEN yok (Hetzner Console → proje → Security → API Tokens, Read & Write)")
    return t


def api(method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    import requests
    r = requests.request(method, f"{API}{path}", headers={"Authorization": f"Bearer {_token()}"}, json=body, timeout=60)
    if r.status_code >= 400:
        raise SystemExit(f"Hetzner API {method} {path}: {r.status_code} {r.text[:300]}")
    return r.json() if r.text else {}


def price(location: str = "nbg1") -> dict[str, Any]:
    st = next(s for s in api("GET", "/pricing")["pricing"]["server_types"] if s["name"] == TYPE)
    p = next(x for x in st["prices"] if x["location"] == location)
    out = {"type": TYPE, "location": location, "hourly_net_eur": float(p["price_hourly"]["net"]),
           "hourly_gross_eur": float(p["price_hourly"]["gross"]), "monthly_net_eur": float(p["price_monthly"]["net"])}
    print(json.dumps(out))
    return out


def ensure_ssh_key() -> int:
    if not KEY_PATH.exists():
        KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "", "-C", NAME, "-f", str(KEY_PATH)], check=True,
                       capture_output=True)
    pub = KEY_PATH.with_suffix(".pub").read_text().strip()
    for k in api("GET", f"/ssh_keys?name={NAME}")["ssh_keys"]:
        return k["id"]
    return api("POST", "/ssh_keys", {"name": NAME, "public_key": pub, "labels": {"proje": NAME}})["ssh_key"]["id"]


def find() -> dict[str, Any] | None:
    s = api("GET", f"/servers?name={NAME}")["servers"]
    return s[0] if s else None


def create(location: str) -> dict[str, Any]:
    if find():
        raise SystemExit(f"{NAME} zaten var: python -m bench.vm.hetzner status")
    key = ensure_ssh_key()
    p = price(location)
    srv = api("POST", "/servers", {"name": NAME, "server_type": TYPE, "image": IMAGE, "location": location,
                                    "ssh_keys": [key], "labels": {"proje": NAME},
                                    "public_net": {"enable_ipv4": True, "enable_ipv6": True}})["server"]
    for _ in range(90):
        s = api("GET", f"/servers/{srv['id']}")["server"]
        if s["status"] == "running":
            break
        time.sleep(5)
    ip = s["public_net"]["ipv4"]["ip"]
    state = {"id": s["id"], "ip": ip, "created": s["created"], "location": location, "price": p}
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1), encoding="utf-8")
    print(json.dumps(state))
    print(f"ssh -i {KEY_PATH} root@{ip}")
    return state


def status() -> None:
    s = find()
    print(json.dumps({"id": s["id"], "status": s["status"], "ip": s["public_net"]["ipv4"]["ip"],
                      "created": s["created"]} if s else {"server": None}))


def delete() -> dict[str, Any]:
    s = find()
    out: dict[str, Any] = {"deleted_at": datetime.now(timezone.utc).isoformat()}
    if s:
        api("DELETE", f"/servers/{s['id']}")
        for _ in range(60):
            if not find():
                break
            time.sleep(3)
        out["server_gone"] = find() is None
        out["created"] = s["created"]
    else:
        out["server_gone"] = True
    for k in api("GET", f"/ssh_keys?name={NAME}")["ssh_keys"]:
        api("DELETE", f"/ssh_keys/{k['id']}")
    out["ssh_key_gone"] = not api("GET", f"/ssh_keys?name={NAME}")["ssh_keys"]
    if STATE.exists():
        st = json.loads(STATE.read_text(encoding="utf-8"))
        STATE.write_text(json.dumps({**st, **out}, indent=1), encoding="utf-8")
    print(json.dumps(out))
    return out


def openrouter_usage(env: str) -> dict[str, Any] | None:
    import requests
    key = os.environ.get(env)
    if not key and os.name == "nt":
        import winreg
        try:
            key = winreg.QueryValueEx(winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment"), env)[0]
        except OSError:
            key = None
    if not key:
        return None
    r = requests.get("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {key}"}, timeout=30)
    d = r.json().get("data", {}) if r.ok else {}
    return {"usage_usd": d.get("usage"), "limit_usd": d.get("limit"), "label": d.get("label")}


def cost(openrouter_env: str) -> dict[str, Any]:
    """Hetzner saatlik faturalar (başlayan saat tam sayılır): ceil(saat) × net saatlik fiyat. KDV hariç."""
    st = json.loads(STATE.read_text(encoding="utf-8"))
    t0 = datetime.fromisoformat(st["created"].replace("Z", "+00:00"))
    t1 = datetime.fromisoformat(st["deleted_at"]) if st.get("deleted_at") else datetime.now(timezone.utc)
    hours = (t1 - t0).total_seconds() / 3600
    eur = math.ceil(hours) * st["price"]["hourly_net_eur"]
    out = {"hours": round(hours, 2), "billed_hours": math.ceil(hours), "hetzner_eur_net": round(eur, 2),
           "openrouter": openrouter_usage(openrouter_env), "server_deleted": bool(st.get("server_gone"))}
    print(json.dumps(out))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("price")
    p.add_argument("--location", default="nbg1")
    c = sub.add_parser("create")
    c.add_argument("--location", default="nbg1")
    sub.add_parser("status")
    sub.add_parser("delete")
    co = sub.add_parser("cost")
    co.add_argument("--openrouter-env", default="OPENROUTER_API_KEY_VM")
    a = ap.parse_args()
    {"price": lambda: price(a.location), "create": lambda: create(a.location), "status": status, "delete": delete,
     "cost": lambda: cost(a.openrouter_env)}[a.cmd]()


if __name__ == "__main__":
    main()
