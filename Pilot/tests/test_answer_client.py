"""Cevap modeli istemcisi (Adım 2 planı §29): yedeğe geçiş, ilk token sınırı, akış bekçisi. Ağsız sahte akışlarla."""
import json

import pytest

from pilot.cloud import AnswerClient, ServiceUnavailable

INDEX = lambda: {"m": {"strict": frozenset({"deepinfra", "venice", "parasail"}), "safety": frozenset()}}


class FakeResp:
    def __init__(self, status=200, events=(), raise_at=None):
        self.status_code, self.text, self.events, self.raise_at = status, "hata", list(events), raise_at

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def iter_lines(self):
        for i, e in enumerate(self.events):
            if self.raise_at == i:
                raise TimeoutError("read timeout")
            yield ("data: " + json.dumps(e)).encode("utf-8")
        yield b"data: [DONE]"


def content(*pieces, finish="stop"):
    ev = [{"choices": [{"delta": {"content": p}}]} for p in pieces]
    return ev + [{"choices": [{"delta": {}, "finish_reason": finish}], "usage": {"cost": 0.001}}]


class FakeSession:
    def __init__(self, by_provider):
        self.by_provider, self.calls = by_provider, []

    def post(self, url, json=None, stream=False, timeout=None):
        p = json["provider"]["order"][0]
        self.calls.append((p, json["provider"], json["max_tokens"], json["reasoning"]))
        return self.by_provider[p]


def client(session, providers=("deepinfra", "venice", "parasail")):
    return AnswerClient("m", providers, {"type": "object"}, 1200, 2.5, 40, session=session, index=INDEX)


def test_primary_answers_and_request_is_pinned():
    s = FakeSession({"deepinfra": FakeResp(events=content('{"tur":', '"cevap"}'))})
    rec = client(s).stream([{"role": "user", "content": "x"}])
    assert rec["provider"] == "deepinfra" and rec["content"] == '{"tur":"cevap"}' and rec["finish"] == "stop"
    assert s.calls == [("deepinfra", s.calls[0][1], 1200, {"enabled": False})]
    assert s.calls[0][1]["allow_fallbacks"] is False and s.calls[0][1]["zdr"] is True
    assert rec["zaman"][-1][1] == len(rec["content"]) and [a["provider"] for a in rec["denemeler"]] == ["deepinfra"]


def test_429_goes_to_first_backup():
    s = FakeSession({"deepinfra": FakeResp(status=429), "venice": FakeResp(events=content("{}"))})
    rec = client(s).stream([])
    assert rec["provider"] == "venice" and rec["denemeler"][0]["err"].startswith("429")


def test_first_token_timeout_goes_to_backup():
    s = FakeSession({"deepinfra": FakeResp(events=content("{}"), raise_at=0), "venice": FakeResp(events=content("{}"))})
    rec = client(s).stream([])
    assert rec["provider"] == "venice" and "TimeoutError" in rec["denemeler"][0]["err"]


def test_runaway_whitespace_triggers_guard_and_next_provider():
    s = FakeSession({"deepinfra": FakeResp(status=503), "venice": FakeResp(events=content('{"a":"b"', " " * 30, " " * 30)),
                     "parasail": FakeResp(events=content('{"a":"b"}'))})
    rec = client(s).stream([])
    assert rec["provider"] == "parasail" and rec["denemeler"][1]["kacak"] is True


def test_short_whitespace_is_not_runaway():
    s = FakeSession({"deepinfra": FakeResp(events=content('{"a":', " " * 40, '"b"}'))})
    assert client(s).stream([])["provider"] == "deepinfra"


def test_all_providers_down_is_service_unavailable_not_local_fallback():
    s = FakeSession({p: FakeResp(status=502) for p in ("deepinfra", "venice", "parasail")})
    with pytest.raises(ServiceUnavailable):
        client(s).stream([])


def test_last_runaway_returns_truncated_record():
    s = FakeSession({"deepinfra": FakeResp(events=content('{"a":"b"', " " * 50))})
    rec = client(s, ("deepinfra",)).stream([])
    assert rec["kacak"] and rec["finish"] == "length"


def test_non_zdr_providers_are_dropped():
    s = FakeSession({"venice": FakeResp(events=content("{}"))})
    c = client(s, ("bilinmeyen", "venice"))
    assert c.providers == ["venice"]
    with pytest.raises(ServiceUnavailable):
        client(s, ("bilinmeyen",))


def test_on_delta_receives_growing_content():
    seen = []
    s = FakeSession({"deepinfra": FakeResp(events=content('{"a":', '"b"}'))})
    client(s).stream([], on_delta=lambda c, t: seen.append(c))
    assert seen == ['{"a":', '{"a":"b"}']


def test_midstream_failure_after_verified_item_does_not_retry():
    s = FakeSession({"deepinfra": FakeResp(events=content('{"a":"b"', " " * 50)), "venice": FakeResp(events=content("{}"))})
    rec = client(s).stream([], on_delta=lambda c, t: None, retry_allowed=lambda: False)
    assert rec["tamamlanamadi"] and [c[0] for c in s.calls] == ["deepinfra"]


def test_midstream_failure_without_verified_item_resets_and_retries():
    resets = []
    s = FakeSession({"deepinfra": FakeResp(events=content('{"a":"b"', " " * 50)), "venice": FakeResp(events=content("{}"))})
    rec = client(s).stream([], on_delta=lambda c, t: None, retry_allowed=lambda: True, on_reset=lambda: resets.append(1))
    assert rec["provider"] == "venice" and resets == [1]
