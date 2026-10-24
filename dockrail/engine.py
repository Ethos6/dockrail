"""Build explicit Docker CLI invocations without shell evaluation."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Sequence


class EngineError(RuntimeError):
    pass


Runner = Callable[..., subprocess.CompletedProcess[str]]


def docker_binary() -> str | None:
    return shutil.which("docker")


def compose_command(
    action: str,
    *,
    target: str | None = None,
    compose_file: Path | str = "compose.yaml",
    project: str,
    service: str | None = None,
    follow: bool = False,
    build: bool = False,
) -> list[str]:
    if action not in {"up", "ps", "logs", "stop", "down"}:
        raise ValueError("unsupported Compose action")
    if service is not None and not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,47}", service):
        raise ValueError("service name contains unsupported characters")
    binary = docker_binary() or "docker"
    command = [binary]
    if target:
        command.extend(["--host", f"ssh://{target}"])
    command.extend(["compose", "--project-name", project, "--file", str(compose_file)])
    if action == "up":
        command.extend(["up", "--detach"])
        if build:
            command.append("--build")
    elif action == "logs":
        command.extend(["logs", "--tail", "100"])
        if follow:
            command.append("--follow")
        if service:
            command.append(service)
    else:
        command.append(action)
    return command


def run(command: Sequence[str], *, cwd: Path, runner: Runner | None = None) -> int:
    """Run a command in the project directory and report helpful failures."""
    runner = runner or subprocess.run
    try:
        result = runner(list(command), cwd=str(cwd), text=True, check=False)
    except FileNotFoundError as exc:
        raise EngineError("Docker CLI was not found. Install Docker Engine and the Compose plugin first.") from exc
    except OSError as exc:
        raise EngineError(f"could not start Docker CLI: {exc}") from exc
    if result.returncode:
        raise EngineError(f"Docker command failed with exit code {result.returncode}")
    return result.returncode


def doctor(*, target: str | None = None, runner: Runner | None = None) -> list[str]:
    runner = runner or subprocess.run
    binary = docker_binary()
    if not binary:
        raise EngineError("Docker CLI was not found on PATH")
    prefix = [binary]
    if target:
        prefix += ["--host", f"ssh://{target}"]
    checks = [("Docker CLI", [binary, "--version"]), ("Compose plugin", prefix + ["compose", "version"]), ("Engine connection", prefix + ["info", "--format", "{{.ServerVersion}}"])]
    completed: list[str] = []
    for label, command in checks:
        try:
            result = runner(command, text=True, check=False, capture_output=True)
        except OSError as exc:
            raise EngineError(f"{label} check could not start: {exc}") from exc
        if result.returncode:
            detail = (result.stderr or result.stdout or "").strip()
            raise EngineError(f"{label} check failed" + (f": {detail}" if detail else ""))
        completed.append(f"{label}: OK")
    if target:
        completed.append("Transport: Docker SSH via OpenSSH; host-key checking remains enabled")
    return completed
