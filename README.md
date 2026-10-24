# DockRail

**Run the same Docker Compose project on your laptop or on a small server.**

DockRail is a lightweight command line helper for Docker Engine. It uses the Docker CLI and Compose plugin you already have, and connects to remote Linux hosts over OpenSSH. The host runs the containers; DockRail adds no daemon, hosted control plane, database, or monthly platform fee.

> Status: early preview. DockRail has been tested with a simulated Docker CLI, not yet against live Docker engines or VPS providers.

## Why DockRail

- **Local and remote from one command:** choose a local engine or a named SSH target.
- **Host anywhere:** use a Linux VPS or server with Docker Engine, Compose, and SSH access.
- **Small server friendly:** only the services in your Compose file run on the server; DockRail itself runs on your workstation.
- **No public Docker socket:** remote requests use Docker's SSH transport through OpenSSH. Keep port 2375 closed.
- **No dependency downloads:** Python 3.9+ standard library only.
- **Conservative lifecycle:** `stop` stops services; `down` removes project containers and its network while keeping named volumes.

## Requirements

- Python 3.9 or newer on the computer where you run DockRail
- Docker CLI with the Compose plugin
- For remote targets: OpenSSH client locally; a reachable Linux host with Docker Engine and Compose installed; SSH public key access and permission to use Docker on that host

DockRail does not install Docker, provision cloud servers, provide a web dashboard, or run containers itself. Server size and cost depend on your VPS provider and workloads. A tiny server can run a small service, but memory-heavy databases, builds, or several services need more resources.

## Install from source

```sh
git clone https://github.com/Ethos6/dockrail.git
cd dockrail
python -m pip install .
```

Or run without installing:

```sh
python -m dockrail --help
```

## Quick start: local

```sh
mkdir hello-dockrail && cd hello-dockrail
dockrail init
dockrail doctor
dockrail deploy
dockrail status
dockrail logs web
dockrail stop
```

`dockrail init` creates a small example Compose file and refuses to overwrite an existing file. The example publishes its HTTP port on `127.0.0.1` only.

## Quick start: a small remote server

First install Docker Engine and the Compose plugin on your Linux server, add your SSH public key, and verify that `ssh user@server.example.com` works. Use a non-root account with Docker access and keep SSH host-key checking enabled.

```sh
dockrail target add tiny-vps deploy@server.example.com
dockrail target list
dockrail doctor --target tiny-vps
dockrail deploy --target tiny-vps
dockrail status --target tiny-vps
```

The project files are read by the local Compose client. Compose sends build context and configuration through Docker's SSH connection. Bind mounts refer to paths on the server, so prefer named volumes for persistent server data. A Compose file can expose ports publicly; inspect its `ports`, `volumes`, `privileged`, and `network_mode` settings before deployment.

## Commands

```text
dockrail init [directory]
dockrail target add NAME SSH_ENDPOINT
dockrail target list
dockrail target remove NAME
dockrail doctor [--target NAME]
dockrail deploy [--target NAME] [--file compose.yaml] [--project NAME] [--build]
dockrail status [--target NAME] [--file compose.yaml] [--project NAME]
dockrail logs [SERVICE] [--follow] [--target NAME] [--file compose.yaml] [--project NAME]
dockrail stop [--target NAME] [--file compose.yaml] [--project NAME]
dockrail down [--target NAME] [--file compose.yaml] [--project NAME]
```

Without `--target`, DockRail uses the local Docker CLI context. It does not switch or edit your global Docker context. A remote target is passed to Docker as `--host ssh://ENDPOINT`; OpenSSH handles authentication and host verification.

`down` intentionally has no volume deletion option. Remove persistent data with your normal Docker administration workflow after you have made and checked a backup.

## Configuration and secrets

Named targets are stored in a small JSON file under the user's config directory (`$XDG_CONFIG_HOME/dockrail/config.json`, otherwise `~/.config/dockrail/config.json`; on Windows, `%APPDATA%\dockrail\config.json`). DockRail writes it with owner-only permissions where supported and does not store private keys, passwords, or environment values. SSH credentials stay with OpenSSH. Keep `.env` files out of Git and manage production secrets using your host's existing secret-handling process.

## Security model

- DockRail invokes the Docker CLI with argument arrays; it does not interpolate commands through a shell.
- Remote Docker access uses SSH. DockRail does not open or configure an unauthenticated TCP daemon.
- SSH host-key verification is left to OpenSSH. DockRail never adds `StrictHostKeyChecking=no` or a password to the command.
- Target strings are validated and cannot inject extra command-line flags.
- `stop` preserves containers and volumes. `down` preserves named and anonymous volumes by omitting `--volumes`.
- Docker access grants powerful control over the host. A user who can control Docker may be able to obtain root-equivalent access; only add trusted targets.
- DockRail does not audit arbitrary Compose files. Review the file before running it, especially for privileged containers, host networking, host bind mounts, and public ports.

## Development

```sh
python -m unittest discover -s tests -v
python -m dockrail --help
```

The tests use a fake Docker executable and make no network or daemon calls. For end-to-end validation, use a disposable local Docker engine and a disposable VPS; those integrations are not claimed by the unit suite.

## Project comparison

| Project | Main focus | How DockRail differs |
| --- | --- | --- |
| [Container Desktop](https://github.com/container-desktop/container-desktop) | Windows Docker workflow backed by WSL2 | DockRail is a small cross-platform CLI for an existing local engine or an SSH-connected server; it does not bundle or manage an engine. |
| [FlyEnv](https://github.com/xpf0000/FlyEnv) | Native management of many runtimes and services | DockRail focuses narrowly on Compose workloads and remote deployment rather than installing local language runtimes. |

DockRail is an independent implementation. It does not bundle either project or copy their source code.

## License

MIT. See [LICENSE](LICENSE).

