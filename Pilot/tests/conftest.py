import pytest


@pytest.fixture
def doc_rules(monkeypatch):
    """Dokümana özgü elle yazılmış kuralların hepsi açık (PILOT_DOC_SPECIFIC_RULES=1): eski davranışı test eden testler."""
    from pilot import config
    monkeypatch.setattr(config, "DOC_SPECIFIC_RULES", frozenset(config.DOC_RULE_NAMES))
