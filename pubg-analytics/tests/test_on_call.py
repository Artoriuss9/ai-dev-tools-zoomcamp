from fastapi.testclient import TestClient

from ops import on_call_agent, restart_proxy
from ops.on_call_agent import Alert


def make_alert(status="firing", fingerprint="a" * 16, endpoint="liveness"):
    return Alert(
        status=status,
        labels={
            "alertname": on_call_agent.ALERT_NAME,
            "job": on_call_agent.ALLOWED_JOB,
            "endpoint": endpoint,
        },
        fingerprint=fingerprint,
    )


def test_responder_does_not_restart_when_readiness_fails_but_liveness_is_ok():
    restart_calls = []
    probe_results = {"health": True, "ready": False}

    result = on_call_agent.respond_to_alert(
        make_alert(),
        probe=lambda url: probe_results[url.rsplit("/", 1)[-1]],
        restart=lambda incident_id: restart_calls.append(incident_id) or (True, "requested"),
        resolve=lambda incident_id: (True, "cleared"),
        wait_for_recovery=lambda: True,
    )

    assert result["action"] == "escalated"
    assert result["reason"] == "readiness_failed_requires_operator"
    assert restart_calls == []


def test_liveness_alert_restarts_app_once_when_app_and_readiness_are_unavailable():
    restart_calls = []

    result = on_call_agent.respond_to_alert(
        make_alert(endpoint="liveness"),
        probe=lambda _: False,
        restart=lambda incident_id: restart_calls.append(incident_id) or (True, "requested"),
        resolve=lambda incident_id: (True, "cleared"),
        wait_for_recovery=lambda: True,
    )

    assert result["action"] == "restarted"
    assert len(restart_calls) == 1


def test_readiness_alert_never_restarts_app():
    restart_calls = []

    result = on_call_agent.respond_to_alert(
        make_alert(endpoint="readiness"),
        probe=lambda _: False,
        restart=lambda incident_id: restart_calls.append(incident_id) or (True, "requested"),
        resolve=lambda incident_id: (True, "cleared"),
        wait_for_recovery=lambda: True,
    )

    assert result["action"] == "escalated"
    assert result["reason"] == "readiness_alert_requires_operator"
    assert restart_calls == []


def test_responder_restarts_only_once_and_checks_recovery():
    restart_calls = []
    probe_results = {"health": False, "ready": True}

    result = on_call_agent.respond_to_alert(
        make_alert(),
        probe=lambda url: probe_results[url.rsplit("/", 1)[-1]],
        restart=lambda incident_id: restart_calls.append(incident_id) or (True, "requested"),
        resolve=lambda incident_id: (True, "cleared"),
        wait_for_recovery=lambda: True,
    )

    assert result["action"] == "restarted"
    assert len(restart_calls) == 1


def test_responder_escalates_after_failed_restart():
    restart_calls = []

    result = on_call_agent.respond_to_alert(
        make_alert(),
        probe=lambda url: url.endswith("/ready"),
        restart=lambda incident_id: restart_calls.append(incident_id) or (True, "requested"),
        resolve=lambda incident_id: (True, "cleared"),
        wait_for_recovery=lambda: False,
    )

    assert result["action"] == "escalated"
    assert result["reason"] == "service_unhealthy_after_restart"
    assert len(restart_calls) == 1


def test_responder_escalates_without_retry_when_incident_already_used_restart():
    restart_calls = []

    result = on_call_agent.respond_to_alert(
        make_alert(),
        probe=lambda url: url.endswith("/ready"),
        restart=lambda incident_id: restart_calls.append(incident_id)
        or (False, "restart_already_used"),
        resolve=lambda incident_id: (True, "cleared"),
        wait_for_recovery=lambda: False,
    )

    assert result["action"] == "escalated"
    assert result["reason"] == "restart_already_used"
    assert len(restart_calls) == 1


def test_http_probe_rejects_non_http_protocols():
    assert on_call_agent.http_probe("file:///C:/Windows/win.ini") is False


def test_restart_proxy_client_uses_bearer_secret(tmp_path, monkeypatch):
    token_path = tmp_path / "restart-token"
    token_path.write_text("local-test-token", encoding="utf-8")
    request_data = {}

    class Response:
        status_code = 200

    def fake_post(url, **kwargs):
        request_data["url"] = url
        request_data.update(kwargs)
        return Response()

    monkeypatch.setattr(on_call_agent.httpx, "post", fake_post)

    result = on_call_agent._proxy_request("/restart-app", "f" * 16, str(token_path))

    assert result == (True, "request_accepted")
    assert request_data["url"] == "http://restart-proxy:8082/restart-app"
    assert request_data["headers"]["Authorization"] == "Bearer local-test-token"


def test_resolved_alert_clears_incident_without_health_checks():
    resolved = []

    result = on_call_agent.respond_to_alert(
        make_alert(status="resolved"),
        probe=lambda _: (_ for _ in ()).throw(AssertionError("must not probe")),
        restart=lambda _: (_ for _ in ()).throw(AssertionError("must not restart")),
        resolve=lambda incident_id: resolved.append(incident_id) or (True, "cleared"),
        wait_for_recovery=lambda: False,
    )

    assert result["action"] == "incident_cleared"
    assert resolved == ["a" * 16]


def test_responder_rejects_unapproved_alert():
    alert = make_alert()
    alert.labels["alertname"] = "UnapprovedAlert"

    try:
        on_call_agent.respond_to_alert(
            alert,
            probe=lambda _: False,
            restart=lambda _: (False, "unused"),
            resolve=lambda _: (True, "unused"),
            wait_for_recovery=lambda: False,
        )
    except ValueError as exc:
        assert "not an approved" in str(exc)
    else:
        raise AssertionError("unapproved alert was accepted")


def test_alert_webhook_requires_bearer_token(tmp_path, monkeypatch):
    token_path = tmp_path / "webhook-token"
    token_path.write_text("local-test-token", encoding="utf-8")
    monkeypatch.setenv("ALERTMANAGER_TOKEN_FILE", str(token_path))
    client = TestClient(on_call_agent.app)
    payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": on_call_agent.ALERT_NAME,
                    "job": on_call_agent.ALLOWED_JOB,
                    "endpoint": "liveness",
                },
                "fingerprint": "a" * 16,
            }
        ]
    }

    assert client.post("/alerts", json=payload).status_code == 401


def test_alert_webhook_runs_bounded_response_for_authenticated_alert(tmp_path, monkeypatch):
    token_path = tmp_path / "webhook-token"
    token_path.write_text("local-test-token", encoding="utf-8")
    monkeypatch.setenv("ALERTMANAGER_TOKEN_FILE", str(token_path))
    monkeypatch.setattr(on_call_agent, "http_probe", lambda url: url.endswith("/ready"))
    monkeypatch.setattr(on_call_agent, "_wait_for_recovery", lambda *args: True)
    restart_routes = []
    monkeypatch.setattr(
        on_call_agent,
        "_proxy_request",
        lambda path, fingerprint, token_file: restart_routes.append(path) or (True, "accepted"),
    )
    client = TestClient(on_call_agent.app)
    response = client.post(
        "/alerts",
        headers={"Authorization": "Bearer local-test-token"},
        json={
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": on_call_agent.ALERT_NAME,
                        "job": on_call_agent.ALLOWED_JOB,
                        "endpoint": "liveness",
                    },
                    "fingerprint": "e" * 16,
                }
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["action"] == "restarted"
    assert restart_routes == ["/restart-app"]


def test_restart_proxy_persists_one_attempt_per_active_incident(tmp_path, monkeypatch):
    token_path = tmp_path / "restart-token"
    token_path.write_text("local-test-token", encoding="utf-8")
    monkeypatch.setattr(restart_proxy, "TOKEN_FILE", str(token_path))
    monkeypatch.setattr(restart_proxy, "STATE_DATABASE", tmp_path / "state.sqlite3")
    restart_calls = []
    monkeypatch.setattr(restart_proxy, "restart_app_container", lambda: restart_calls.append("app"))
    client = TestClient(restart_proxy.app)
    headers = {"Authorization": "Bearer local-test-token"}
    payload = {"incident_id": "b" * 16}

    assert client.post("/restart-app", json=payload, headers=headers).status_code == 200
    assert client.post("/restart-app", json=payload, headers=headers).status_code == 409
    assert restart_calls == ["app"]

    assert client.post("/resolve", json=payload, headers=headers).status_code == 200
    assert client.post("/restart-app", json=payload, headers=headers).status_code == 200
    assert restart_calls == ["app", "app"]


def test_restart_proxy_records_failed_attempt_and_does_not_retry(tmp_path, monkeypatch):
    token_path = tmp_path / "restart-token"
    token_path.write_text("local-test-token", encoding="utf-8")
    monkeypatch.setattr(restart_proxy, "TOKEN_FILE", str(token_path))
    monkeypatch.setattr(restart_proxy, "STATE_DATABASE", tmp_path / "state.sqlite3")
    restart_calls = []

    def fail_restart():
        restart_calls.append("app")
        raise RuntimeError("Docker daemon unavailable")

    monkeypatch.setattr(restart_proxy, "restart_app_container", fail_restart)
    client = TestClient(restart_proxy.app)
    headers = {"Authorization": "Bearer local-test-token"}
    payload = {"incident_id": "c" * 16}

    assert client.post("/restart-app", json=payload, headers=headers).status_code == 502
    assert client.post("/restart-app", json=payload, headers=headers).status_code == 409
    assert restart_calls == ["app"]


def test_restart_proxy_rejects_unauthorized_request(tmp_path, monkeypatch):
    token_path = tmp_path / "restart-token"
    token_path.write_text("local-test-token", encoding="utf-8")
    monkeypatch.setattr(restart_proxy, "TOKEN_FILE", str(token_path))
    monkeypatch.setattr(restart_proxy, "STATE_DATABASE", tmp_path / "state.sqlite3")
    restart_calls = []
    monkeypatch.setattr(restart_proxy, "restart_app_container", lambda: restart_calls.append("app"))

    response = TestClient(restart_proxy.app).post(
        "/restart-app",
        json={"incident_id": "d" * 16},
    )

    assert response.status_code == 401
    assert restart_calls == []
