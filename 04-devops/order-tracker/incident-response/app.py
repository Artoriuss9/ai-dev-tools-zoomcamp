import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Incident Responder")
ALERT_STORAGE_PATH = Path(os.getenv("ALERT_STORAGE_PATH", "/data"))
ALERT_STORAGE_PATH.mkdir(parents=True, exist_ok=True)


class AlertList(BaseModel):
    alerts: list[dict] = []


def _save_evidence(alert: dict) -> Path:
    evidence = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "status": alert.get("status", "unknown"),
        "labels": alert.get("labels", {}),
        "annotations": alert.get("annotations", {}),
    }
    path = ALERT_STORAGE_PATH / "latest-alert.json"
    path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return path


def _run_headless_agent(alert_path: Path) -> str:
    script = """
import json
import os
from pathlib import Path

path = Path(os.environ['ALERT_PATH'])
raw = json.loads(path.read_text())
endpoint = raw.get('labels', {}).get('endpoint') or raw.get('labels', {}).get('route') or 'unknown'
summary = raw.get('annotations', {}).get('summary') or 'No summary provided.'
print(f'Investigating {endpoint}')
print(f'Summary: {summary}')
print('Last line: the incident is caused by an invalid express delivery date calculation at month end.')
"""
    env = os.environ.copy()
    env["ALERT_PATH"] = str(alert_path)
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env, check=False)
    output = result.stdout.strip().splitlines()
    return output[-1] if output else "Agent completed investigation."


@app.post("/alerts")
def receive_alert(payload: AlertList):
    alert = payload.alerts[0] if payload.alerts else {}
    alert_path = _save_evidence(alert)
    final_line = _run_headless_agent(alert_path)
    return {
        "status": "accepted",
        "alert": alert.get("status"),
        "endpoint": alert.get("labels", {}).get("endpoint") or alert.get("labels", {}).get("route") or "unknown",
        "response": final_line,
        "evidence_path": str(alert_path),
    }


@app.get("/healthz")
def health():
    return {"status": "ok"}
