import http.client
import json
import logging
import os
import re
import secrets
import socket
import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field


STATE_DATABASE = Path(os.getenv("RESTART_STATE_DATABASE", "/data/restart-proxy.sqlite3"))
TOKEN_FILE = os.getenv("RESTART_PROXY_TOKEN_FILE", "/run/secrets/restart_proxy_token")
FINGERPRINT_PATTERN = re.compile(r"^[0-9a-f]{16}$")
logger = logging.getLogger("pubg_analytics.restart_proxy")


class IncidentRequest(BaseModel):
    incident_id: str = Field(pattern=r"^[0-9a-f]{16}$")


class DockerSocketConnection(http.client.HTTPConnection):
    def connect(self) -> None:
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(os.getenv("DOCKER_SOCKET", "/var/run/docker.sock"))


def _read_secret() -> str:
    try:
        secret = Path(TOKEN_FILE).read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise HTTPException(status_code=503, detail="Restart proxy secret is unavailable") from exc
    if not secret:
        raise HTTPException(status_code=503, detail="Restart proxy secret is empty")
    return secret


def _authorized(request: Request) -> bool:
    expected = _read_secret()
    scheme, separator, supplied = request.headers.get("authorization", "").partition(" ")
    return bool(separator and scheme.lower() == "bearer") and secrets.compare_digest(expected, supplied)


def _connect_state() -> sqlite3.Connection:
    STATE_DATABASE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(STATE_DATABASE, timeout=5)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS incident_restarts (
            incident_id TEXT PRIMARY KEY,
            attempted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            outcome TEXT NOT NULL DEFAULT 'attempted'
        )
        """
    )
    return connection


def _claim_incident(incident_id: str) -> bool:
    with closing(_connect_state()) as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO incident_restarts (incident_id) VALUES (?)",
                (incident_id,),
            )
            connection.commit()
            return True
        except sqlite3.IntegrityError:
            connection.rollback()
            return False


def _record_outcome(incident_id: str, outcome: str) -> None:
    with closing(_connect_state()) as connection:
        connection.execute(
            "UPDATE incident_restarts SET outcome = ? WHERE incident_id = ?",
            (outcome, incident_id),
        )
        connection.commit()


def _clear_incident(incident_id: str) -> None:
    with closing(_connect_state()) as connection:
        connection.execute("DELETE FROM incident_restarts WHERE incident_id = ?", (incident_id,))
        connection.commit()


def restart_app_container() -> None:
    connection = DockerSocketConnection("localhost", timeout=5)
    try:
        connection.request(
            "POST",
            "/v1.41/containers/pubg-analytics-app/restart?t=10",
        )
        response = connection.getresponse()
        response.read()
        if response.status not in {200, 204}:
            raise RuntimeError(f"Docker restart request failed with HTTP {response.status}")
    finally:
        connection.close()


app = FastAPI(title="PUBG Analytics Restart Proxy", docs_url=None, redoc_url=None)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/restart-app")
def restart_app(payload: IncidentRequest, request: Request) -> dict[str, str]:
    if not _authorized(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not FINGERPRINT_PATTERN.fullmatch(payload.incident_id):
        raise HTTPException(status_code=422, detail="Invalid incident ID")
    if not _claim_incident(payload.incident_id):
        raise HTTPException(status_code=409, detail="Restart already attempted for this incident")

    try:
        restart_app_container()
    except (http.client.HTTPException, OSError, RuntimeError, TimeoutError) as exc:
        _record_outcome(payload.incident_id, "failed")
        logger.error(
            json.dumps(
                {
                    "incident_id": payload.incident_id,
                    "action": "restart_failed",
                    "error": str(exc),
                },
                sort_keys=True,
            )
        )
        raise HTTPException(status_code=502, detail="Application restart failed; escalate to an operator") from exc

    _record_outcome(payload.incident_id, "restarted")
    logger.info(
        json.dumps(
            {"incident_id": payload.incident_id, "action": "app_restart_requested"},
            sort_keys=True,
        )
    )
    return {"status": "restart_requested"}


@app.post("/resolve")
def resolve_incident(payload: IncidentRequest, request: Request) -> dict[str, str]:
    if not _authorized(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not FINGERPRINT_PATTERN.fullmatch(payload.incident_id):
        raise HTTPException(status_code=422, detail="Invalid incident ID")
    _clear_incident(payload.incident_id)
    return {"status": "incident_cleared"}


def main() -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    # The listener is internal to Compose and has no published host port.
    uvicorn.run(app, host="0.0.0.0", port=8082)  # nosec B104


if __name__ == "__main__":
    main()
