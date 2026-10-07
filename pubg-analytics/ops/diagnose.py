import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_SERVICES = {"app", "otel-collector", "prometheus", "loki", "tempo", "grafana"}


def check_http(url: str) -> dict[str, object]:
    try:
        with urlopen(url, timeout=3) as response:
            return {
                "status": "ok" if response.status == 200 else "failed",
                "http_status": response.status,
            }
    except HTTPError as exc:
        return {"status": "failed", "http_status": exc.code, "error": str(exc)}
    except (URLError, TimeoutError, OSError) as exc:
        return {"status": "failed", "error": str(exc)}


def check_compose() -> dict[str, object]:
    docker = shutil.which("docker")
    if not docker:
        return {"status": "unavailable", "error": "Docker CLI is not installed"}
    try:
        result = subprocess.run(
            [docker, "compose", "ps", "--format", "json"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "unavailable", "error": str(exc)}
    if result.returncode:
        return {
            "status": "unavailable",
            "error": result.stderr.strip() or "docker compose ps failed",
        }
    output = result.stdout.strip()
    try:
        payload = json.loads(output) if output else []
    except json.JSONDecodeError:
        try:
            payload = [json.loads(line) for line in output.splitlines() if line.strip()]
        except json.JSONDecodeError as exc:
            return {"status": "failed", "error": f"Invalid Compose status output: {exc}"}
    services = [payload] if isinstance(payload, dict) else payload
    if not isinstance(services, list) or not all(isinstance(item, dict) for item in services):
        return {"status": "failed", "error": "Compose status output must contain service objects"}
    normalized_services = [
        {
            "name": item.get("Service") or item.get("Name"),
            "state": item.get("State"),
            "health": item.get("Health"),
        }
        for item in services
    ]
    observed_names = {item["name"] for item in normalized_services}
    missing_services = sorted(EXPECTED_SERVICES - observed_names)
    healthy = all(
        item["state"] == "running" and item["health"] not in {"starting", "unhealthy"}
        for item in normalized_services
    )
    return {
        "status": "ok" if not missing_services and healthy else "failed",
        "missing_services": missing_services,
        "services": normalized_services,
    }


def build_report(base_url: str, include_compose: bool = True) -> dict[str, object]:
    base_url = base_url.rstrip("/")
    checks = {}
    if include_compose:
        checks["compose"] = check_compose()
    checks["liveness"] = check_http(f"{base_url}/health")
    checks["readiness"] = check_http(f"{base_url}/ready")
    status = "ok" if all(result["status"] == "ok" for result in checks.values()) else "failed"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "status": status,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check PUBG Analytics service and Docker Compose health.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, help="Optional path to write the JSON report.")
    parser.add_argument("--skip-compose", action="store_true", help="Check HTTP endpoints only.")
    args = parser.parse_args()

    report = build_report(args.base_url, include_compose=not args.skip_compose)
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
