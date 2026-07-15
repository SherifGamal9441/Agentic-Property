"""Read-only recruiter-demo preflight. It never prints configuration values."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.pydantic.settings import settings


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def _endpoint() -> str:
    if settings.llm_provider == "ollama":
        return settings.ollama_base_url
    if settings.llm_provider == "vllm":
        return settings.vllm_base_url
    if settings.llm_provider == "custom_openai_compatible_endpoint":
        return settings.custom_openai_base_url
    return "https://api.groq.com/openai/v1"


def _reachable(url: str) -> bool:
    target = url.rstrip("/") + ("/api/tags" if settings.llm_provider == "ollama" else "/models")
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"} if settings.llm_provider == "groq" and settings.groq_api_key else {}
    try:
        with urlopen(Request(target, headers=headers), timeout=2):
            return True
    except HTTPError as error:
        return error.code < 500
    except Exception:
        return False


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dvc_expected(pointer: Path) -> tuple[str, int]:
    data = pointer.read_text(encoding="utf-8")
    md5 = next(line.split(":", 1)[1].strip() for line in data.splitlines() if line.strip().startswith("- md5:"))
    size = int(next(line.split(":", 1)[1].strip() for line in data.splitlines() if line.strip().startswith("size:")))
    return md5, size


def _port_available(port: int) -> bool:
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def run_checks() -> list[Check]:
    checks: list[Check] = []
    errors = settings.provider_errors()
    checks.append(Check("provider configuration", not errors, "valid" if not errors else " ".join(errors)))
    provider_reachable = _reachable(_endpoint()) if not errors else False
    checks.append(Check("provider endpoint", provider_reachable, "reachable" if provider_reachable else "not reachable"))
    for name in ("active_dld.csv", "historical_dld.csv"):
        data, pointer = ROOT / "data" / name, ROOT / "data" / f"{name}.dvc"
        if not data.exists() or not pointer.exists():
            checks.append(Check(name, False, "DVC output or pointer is missing; run dvc pull."))
            continue
        expected_md5, expected_size = _dvc_expected(pointer)
        valid = data.stat().st_size == expected_size and _md5(data) == expected_md5
        checks.append(Check(name, valid, "checksum verified" if valid else "checksum mismatch; run dvc pull."))
    docker = shutil.which("docker")
    docker_ok = bool(docker and subprocess.run([docker, "compose", "config", "--quiet"], cwd=ROOT, capture_output=True).returncode == 0)
    checks.append(Check("Docker Compose", docker_ok, "configuration valid" if docker_ok else "Docker unavailable or Compose configuration invalid"))
    service_health: dict[int, bool] = {}
    for port, name, url in ((8000, "data service", "http://localhost:8000/health"), (8002, "agent API", "http://localhost:8002/health")):
        try:
            with urlopen(url, timeout=2) as response:
                healthy = json.loads(response.read()).get("status") == "ok"
        except Exception:
            healthy = False
        service_health[port] = healthy
        checks.append(Check(name, healthy, "healthy" if healthy else "not running (acceptable before startup)"))
    try:
        with urlopen("http://localhost:5173", timeout=2) as response:
            service_health[5173] = response.status == 200
    except Exception:
        service_health[5173] = False
    conflicts = [port for port in (5173, 8000, 8002) if not _port_available(port) and not service_health[port]]
    checks.append(Check("demo ports", not conflicts, "available or occupied by healthy Aizen services" if not conflicts else f"conflicts: {', '.join(map(str, conflicts))}"))
    return checks


def main() -> int:
    checks = run_checks()
    for check in checks:
        print(f"[{'PASS' if check.ok else 'FAIL'}] {check.name}: {check.detail}")
    required = [check for check in checks if check.name not in {"data service", "agent API"}]
    return 0 if all(check.ok for check in required) else 1


if __name__ == "__main__":
    sys.exit(main())
