import json
import logging
import os
import re
import secrets
import time
from pathlib import Path
from typing import Callable

import httpx
from fastapi import FastAPI, HTTPException, Request as FastAPIRequest
from pydantic import BaseModel, Field


ALERT_NAME = "PUBGAnalyticsEndpointUnavailable"
ALLOWED_JOB = "pubg-analytics-health"
ALLOWED_ENDPOINTS = {"liveness", "readiness"}
APP_URL = "http://app:8000"
RESTART_PROXY_URL = "http://restart-proxy:8082"
FINGERPRINT_PATTERN = re.compile(r"^[0-9a-f]{16}$")
logger = logging.getLogger("pubg_analytics.on_call")


class Alert(BaseModel):
    status: str
    labels: dict[str, str]
    fingerprint: str = Field(pattern=r"^[0-9a-f]{16}$")


class AlertmanagerWebhook(BaseModel):
    alerts: list[Alert]


def _read_secret(path: str) -> str:
    try:
        secret = Path(path).read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise HTTPException(status_code=503, detail="Required responder secret is unavailable") from exc
    if not secret:
        raise HTTPException(status_code=503, detail="Required responder secret is empty")
    return secret


def _authorized(request: FastAPIRequest, secret_path: str) -> bool:
    expected = _read_secret(secret_path)
    authorization = request.headers.get("authorization", "")
    scheme, separator, supplied = authorization.partition(" ")
    return bool(separator and scheme.lower() == "bearer") and secrets.compare_digest(expected, supplied)


def http_probe(url: str, timeout: float = 2.0) -> bool:
    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=False)
        return 200 <= response.status_code < 300
    except httpx.HTTPError:
        return False


def _proxy_request(path: str, fingerprint: str, token_path: str) -> tuple[bool, str]:
    token = _read_secret(token_path)
    try:
        response = httpx.post(
            f"{RESTART_PROXY_URL}{path}",
            json={"incident_id": fingerprint},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
            follow_redirects=False,
        )
        if response.status_code == 409:
            return False, "restart_already_used"
        if not 200 <= response.status_code < 300:
            return False, f"restart_proxy_http_{response.status_code}"
        return True, "request_accepted"
    except httpx.HTTPError:
        return False, "restart_proxy_unavailable"


def _wait_for_recovery(
    probe: Callable[[str], bool],
    base_url: str,
    timeout: float = 30.0,
) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if probe(f"{base_url}/health") and probe(f"{base_url}/ready"):
            return True
        time.sleep(2)
    return False


def respond_to_alert(
    alert: Alert,
    *,
    probe: Callable[[str], bool] = http_probe,
    restart: Callable[[str], tuple[bool, str]],
    resolve: Callable[[str], tuple[bool, str]],
    wait_for_recovery: Callable[[], bool],
) -> dict[str, str]:
    if (
        alert.labels.get("alertname") != ALERT_NAME
        or alert.labels.get("job") != ALLOWED_JOB
        or alert.labels.get("endpoint") not in ALLOWED_ENDPOINTS
    ):
        raise ValueError("Alert is not an approved PUBG Analytics health alert")

    fingerprint = alert.fingerprint
    if not FINGERPRINT_PATTERN.fullmatch(fingerprint):
        raise ValueError("Alert fingerprint has an invalid format")

    if alert.status == "resolved":
        cleared, reason = resolve(fingerprint)
        return {
            "incident_id": fingerprint,
            "action": "incident_cleared" if cleared else "escalated",
            "reason": reason,
        }
    if alert.status != "firing":
        raise ValueError("Alert status must be firing or resolved")

    base_url = APP_URL
    health_ok = probe(f"{base_url}/health")
    readiness_ok = probe(f"{base_url}/ready")

    if health_ok and readiness_ok:
        return {"incident_id": fingerprint, "action": "no_action", "reason": "service_recovered"}
    if alert.labels["endpoint"] == "readiness":
        return {
            "incident_id": fingerprint,
            "action": "escalated",
            "reason": "readiness_alert_requires_operator",
        }
    if health_ok:
        return {
            "incident_id": fingerprint,
            "action": "escalated",
            "reason": "readiness_failed_requires_operator",
        }

    restarted, reason = restart(fingerprint)
    if not restarted:
        return {"incident_id": fingerprint, "action": "escalated", "reason": reason}
    if wait_for_recovery():
        return {"incident_id": fingerprint, "action": "restarted", "reason": "service_recovered"}
    return {"incident_id": fingerprint, "action": "escalated", "reason": "service_unhealthy_after_restart"}


app = FastAPI(title="PUBG Analytics On-call Agent", docs_url=None, redoc_url=None)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/alerts")
def receive_alert(payload: AlertmanagerWebhook, request: FastAPIRequest) -> dict[str, list[dict[str, str]]]:
    if not _authorized(request, os.getenv("ALERTMANAGER_TOKEN_FILE", "/run/secrets/on_call_webhook_token")):
        raise HTTPException(status_code=401, detail="Unauthorized")

    results = []
    for alert in payload.alerts:
        try:
            result = respond_to_alert(
                alert,
                restart=lambda fingerprint: _proxy_request(
                    "/restart-app",
                    fingerprint,
                    os.getenv("RESTART_PROXY_TOKEN_FILE", "/run/secrets/restart_proxy_token"),
                ),
                resolve=lambda fingerprint: _proxy_request(
                    "/resolve",
                    fingerprint,
                    os.getenv("RESTART_PROXY_TOKEN_FILE", "/run/secrets/restart_proxy_token"),
                ),
                wait_for_recovery=lambda: _wait_for_recovery(
                    http_probe,
                    APP_URL,
                ),
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        logger.info(json.dumps(result, sort_keys=True))
        results.append(result)
    return {"results": results}


def main() -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    # The listener is internal to Compose and has no published host port.
    uvicorn.run(app, host="0.0.0.0", port=8081)  # nosec B104


if __name__ == "__main__":
    main()
