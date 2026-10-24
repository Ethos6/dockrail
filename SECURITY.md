# Security policy

## Reporting a vulnerability

Please do not publish an exploitable vulnerability in an issue. Use GitHub's private vulnerability reporting for this repository, or contact the maintainer through the address on the Ethos6 GitHub profile. Include the affected version, reproduction steps, and impact.

## Scope

DockRail runs the Docker CLI with the current user's permissions. Docker access can grant root-equivalent access on a machine. Remote access depends on OpenSSH and Docker's SSH transport; DockRail does not bypass SSH host verification or store credentials.

DockRail does not validate whether an arbitrary Compose file is safe. Review every Compose file before deployment, especially privileged mode, host mounts, host networking, exposed ports, and secrets.
