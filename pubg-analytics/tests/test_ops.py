from ops import diagnose


def test_build_report_requires_all_health_checks_to_pass(monkeypatch):
    monkeypatch.setattr(diagnose, "check_compose", lambda: {"status": "ok"})
    monkeypatch.setattr(
        diagnose,
        "check_http",
        lambda url: {"status": "ok" if url.endswith("/health") else "failed"},
    )

    report = diagnose.build_report("http://localhost:8000/", include_compose=False)

    assert report["base_url"] == "http://localhost:8000"
    assert report["status"] == "failed"
    assert report["checks"]["readiness"]["status"] == "failed"


def test_compose_check_detects_missing_service(monkeypatch):
    class Completed:
        returncode = 0
        stdout = '{"Service":"app","State":"running","Health":"healthy"}\n'
        stderr = ""

    monkeypatch.setattr(diagnose.shutil, "which", lambda _: "docker")
    monkeypatch.setattr(diagnose.subprocess, "run", lambda *args, **kwargs: Completed())

    result = diagnose.check_compose()

    assert result["status"] == "failed"
    assert "grafana" in result["missing_services"]
