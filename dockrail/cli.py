"""Command line interface for DockRail."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from . import __version__
from . import config
from .engine import EngineError, compose_command, doctor, run

EXAMPLE_COMPOSE = """services:
  web:
    image: nginx:alpine
    ports:
      - \"127.0.0.1:8080:80\"
    restart: unless-stopped
"""


def project_name(path: Path) -> str:
    value = re.sub(r"[^a-z0-9_-]+", "-", path.resolve().name.lower()).strip("-_")
    value = value or "dockrail-app"
    return value[:48]


def add_target_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", help="named SSH target; omit to use the local Docker context")


def add_compose_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--file", default="compose.yaml", help="Compose file path (default: compose.yaml)")
    parser.add_argument("--project", help="Compose project name (defaults to the current directory name)")
    add_target_argument(parser)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dockrail", description="Run Docker Compose locally or on an SSH-connected server.")
    parser.add_argument("--version", action="version", version=f"DockRail {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="create a small example Compose project")
    init.add_argument("directory", nargs="?", default=".")

    target = subparsers.add_parser("target", help="manage named SSH Docker hosts")
    target_sub = target.add_subparsers(dest="target_command", required=True)
    add = target_sub.add_parser("add", help="save an SSH endpoint")
    add.add_argument("name")
    add.add_argument("endpoint", help="host, OpenSSH alias, or user@host[:port]")
    listing = target_sub.add_parser("list", help="list saved targets")
    listing.set_defaults()
    remove = target_sub.add_parser("remove", help="remove a saved target")
    remove.add_argument("name")

    check = subparsers.add_parser("doctor", help="check Docker CLI, Compose, and engine connectivity")
    add_target_argument(check)

    deploy = subparsers.add_parser("deploy", help="build and start a Compose project")
    add_compose_arguments(deploy)
    deploy.add_argument("--build", action="store_true", help="build images before starting")

    for command, help_text in (("status", "show project containers"), ("stop", "stop project containers"), ("down", "remove project containers and network; keep volumes")):
        cmd = subparsers.add_parser(command, help=help_text)
        add_compose_arguments(cmd)

    logs = subparsers.add_parser("logs", help="show project logs")
    add_compose_arguments(logs)
    logs.add_argument("service", nargs="?", help="optional service name")
    logs.add_argument("--follow", action="store_true", help="follow new log output")
    return parser


def resolve_target(name: str | None) -> str | None:
    if not name:
        return None
    targets = config.read_config()["targets"]
    if name not in targets:
        raise ValueError(f"unknown target {name!r}; use `dockrail target list`")
    return targets[name]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            directory = Path(args.directory).expanduser().resolve()
            directory.mkdir(parents=True, exist_ok=True)
            compose_file = directory / "compose.yaml"
            if compose_file.exists():
                raise ValueError(f"refusing to overwrite {compose_file}")
            compose_file.write_text(EXAMPLE_COMPOSE, encoding="utf-8")
            print(f"Created {compose_file}")
            return 0

        if args.command == "target":
            data = config.read_config()
            if args.target_command == "add":
                config.validate_name(args.name)
                endpoint = config.validate_endpoint(args.endpoint)
                data["targets"][args.name] = endpoint
                config.write_config(data)
                print(f"Saved target {args.name}: {endpoint}")
            elif args.target_command == "list":
                if not data["targets"]:
                    print("No saved targets. Add one with `dockrail target add NAME user@host`.")
                for name, endpoint in sorted(data["targets"].items()):
                    print(f"{name}\t{endpoint}")
            else:
                if args.name not in data["targets"]:
                    raise ValueError(f"unknown target {args.name!r}")
                del data["targets"][args.name]
                config.write_config(data)
                print(f"Removed target {args.name}")
            return 0

        target = resolve_target(args.target)
        if args.command == "doctor":
            for line in doctor(target=target):
                print(line)
            return 0

        compose_file = Path(args.file).expanduser()
        if not compose_file.is_absolute():
            compose_file = Path.cwd() / compose_file
        compose_file = compose_file.resolve()
        if not compose_file.is_file():
            raise ValueError(f"Compose file not found: {compose_file}")
        project = args.project or project_name(Path.cwd())
        if not config.NAME_RE.fullmatch(project):
            raise ValueError("project name must be 1-48 letters, digits, dots, underscores, or hyphens")

        action = {"deploy": "up", "status": "ps", "logs": "logs", "stop": "stop", "down": "down"}[args.command]
        command = compose_command(
            action,
            target=target,
            compose_file=compose_file,
            project=project,
            service=getattr(args, "service", None),
            follow=getattr(args, "follow", False),
            build=getattr(args, "build", False),
        )
        return run(command, cwd=Path.cwd())
    except (ValueError, EngineError, OSError) as exc:
        print(f"dockrail: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
