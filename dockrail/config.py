"""Safe, dependency-free storage for SSH target names."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,47}$")
HOST_RE = re.compile(r"^(?:[a-zA-Z0-9][a-zA-Z0-9.-]*)(?::[0-9]{1,5})?$")
USER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_.-]*$")


def config_path() -> Path:
    if os.name == "nt":
        root = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(root) / "dockrail" / "config.json"
    root = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(root) / "dockrail" / "config.json"


def validate_name(name: str) -> str:
    if not NAME_RE.fullmatch(name):
        raise ValueError("target name must be 1-48 letters, digits, dots, underscores, or hyphens")
    return name


def validate_endpoint(endpoint: str) -> str:
    """Accept a host, OpenSSH config alias, or user@host[:port], never CLI flags."""
    if not endpoint or endpoint.startswith("-") or any(ch.isspace() for ch in endpoint):
        raise ValueError("SSH endpoint must be a host or user@host[:port], with no spaces")
    if endpoint.count("@") > 1 or any(ch in endpoint for ch in "`$;&|<>\\\"'(){}[]"):
        raise ValueError("SSH endpoint contains unsupported characters")
    user, sep, host = endpoint.rpartition("@")
    if sep and not USER_RE.fullmatch(user):
        raise ValueError("SSH username contains unsupported characters")
    if not HOST_RE.fullmatch(host):
        raise ValueError("SSH host must be a hostname, IPv4 address, or OpenSSH config alias; IPv6 is not supported yet")
    if ":" in host:
        port_text = host.rsplit(":", 1)[1]
        if not 1 <= int(port_text) <= 65535:
            raise ValueError("SSH port must be between 1 and 65535")
    if ".." in host or host.startswith(".") or host.endswith("."):
        raise ValueError("SSH hostname is invalid")
    return endpoint


def read_config(path: Path | None = None) -> dict[str, Any]:
    target_path = path or config_path()
    try:
        data = json.loads(target_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"version": 1, "targets": {}}
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"cannot read DockRail config at {target_path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("targets"), dict):
        raise ValueError(f"DockRail config at {target_path} has an unsupported format")
    targets: dict[str, str] = {}
    for name, endpoint in data["targets"].items():
        validate_name(name)
        validate_endpoint(endpoint)
        targets[name] = endpoint
    return {"version": 1, "targets": targets}


def write_config(data: dict[str, Any], path: Path | None = None) -> None:
    target_path = path or config_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="config.", dir=target_path.parent, text=True)
    try:
        if os.name != "nt":
            os.chmod(temporary, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target_path)
        if os.name != "nt":
            os.chmod(target_path, 0o600)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
