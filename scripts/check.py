#!/usr/bin/env python3
"""Check public HTTPS endpoints and write a static status snapshot."""

from __future__ import annotations

import argparse
import json
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def gatus_is_fresh(body: str, maximum_age: int, endpoint_name: str) -> bool:
    endpoints = json.loads(body)
    if not isinstance(endpoints, list) or not endpoints:
        return False
    now = datetime.now(timezone.utc)
    selected = [item for item in endpoints if item.get("name") == endpoint_name]
    if len(selected) != 1:
        return False
    for endpoint in selected:
        timestamps = []
        for result in endpoint.get("results", []):
            value = result.get("timestamp")
            if not value:
                continue
            timestamps.append(datetime.fromisoformat(value.replace("Z", "+00:00")))
        if not timestamps or (now - max(timestamps)).total_seconds() > maximum_age:
            return False
    return True


def check_service(service: dict, context: ssl.SSLContext) -> dict:
    started = time.monotonic()
    status = None
    error = None
    healthy = False
    try:
        request = urllib.request.Request(
            service["url"],
            headers={"User-Agent": "minty-status/1.0"},
        )
        with urllib.request.urlopen(request, timeout=15, context=context) as response:
            status = response.status
            body = response.read(1_048_576).decode("utf-8", errors="replace")
        healthy = status in service["statuses"] and (
            not service.get("contains") or service["contains"] in body
        )
        if healthy and service.get("gatus_freshness_seconds"):
            healthy = gatus_is_fresh(
                body,
                service["gatus_freshness_seconds"],
                service["gatus_freshness_endpoint"],
            )
        if not healthy:
            error = "Unexpected response"
    except urllib.error.HTTPError as exc:
        status = exc.code
        error = f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, ssl.SSLError) as exc:
        error = type(exc).__name__

    return {
        "name": service["name"],
        "url": service["url"],
        "healthy": healthy,
        "status": status,
        "latency_ms": round((time.monotonic() - started) * 1000),
        "error": error,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--health-file", type=Path, required=True)
    args = parser.parse_args()

    services = json.loads((ROOT / "checks.json").read_text())
    context = ssl.create_default_context()
    results = [check_service(service, context) for service in services]
    healthy = all(result["healthy"] for result in results)
    snapshot = {
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "healthy": healthy,
        "services": results,
    }
    args.output.write_text(json.dumps(snapshot, indent=2) + "\n")
    args.health_file.write_text("true\n" if healthy else "false\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
