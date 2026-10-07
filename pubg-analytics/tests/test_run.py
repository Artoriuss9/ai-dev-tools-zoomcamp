import pytest

from backend import run


def test_main_uses_platform_port(monkeypatch):
    captured = {}
    monkeypatch.setenv("PORT", "8123")
    monkeypatch.setattr(run.uvicorn, "run", lambda *args, **kwargs: captured.update(kwargs))

    run.main()

    assert captured == {"host": "0.0.0.0", "port": 8123}


def test_main_rejects_invalid_port(monkeypatch):
    monkeypatch.setenv("PORT", "70000")
    with pytest.raises(ValueError, match="PORT must be between"):
        run.main()
