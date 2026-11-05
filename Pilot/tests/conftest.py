import pytest


@pytest.fixture
def doc_rules(monkeypatch):
    """Dokümana özgü elle yazılmış kurallar açık (PILOT_DOC_SPECIFIC_RULES=1): eski davranışı test eden testler için."""
    from pilot import config
    monkeypatch.setattr(config, "DOC_SPECIFIC_RULES", True)
