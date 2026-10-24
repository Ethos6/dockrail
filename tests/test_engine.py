import unittest
from unittest.mock import patch
from pathlib import Path

from dockrail.engine import EngineError, compose_command, doctor


class EngineCommandTests(unittest.TestCase):
    def test_local_deploy_never_adds_remote_host(self):
        with patch("dockrail.engine.docker_binary", return_value=None):
            command = compose_command("up", project="demo", compose_file="compose.yaml", build=True)
        self.assertEqual(command[0], "docker")
        self.assertNotIn("--host", command)
        self.assertEqual(command[-3:], ["up", "--detach", "--build"])

    def test_remote_deploy_uses_ssh_and_no_shell(self):
        with patch("dockrail.engine.docker_binary", return_value=None):
            command = compose_command("up", target="deploy@host.example", project="demo", compose_file="compose.yaml")
        self.assertEqual(command[:4], ["docker", "--host", "ssh://deploy@host.example", "compose"])
        self.assertNotIn("sh", command)

    def test_down_preserves_volumes(self):
        command = compose_command("down", target="host", project="demo")
        self.assertEqual(command[-1], "down")
        self.assertNotIn("--volumes", command)
        self.assertNotIn("-v", command)

    def test_logs_are_bounded_by_default(self):
        command = compose_command("logs", project="demo", service="web")
        self.assertIn("--tail", command)
        self.assertIn("100", command)
        self.assertEqual(command[-1], "web")

    def test_unsupported_command_rejected(self):
        with self.assertRaises(ValueError):
            compose_command("prune", project="demo")

    def test_log_service_cannot_become_an_option(self):
        with self.assertRaises(ValueError):
            compose_command("logs", project="demo", service="--volumes")

    def test_doctor_checks_cli_compose_and_engine_for_remote_target(self):
        seen = []

        def fake_run(command, **kwargs):
            seen.append(command)
            return type("Result", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

        with patch("dockrail.engine.docker_binary", return_value="/fake/docker"):
            results = doctor(target="deploy@host.example", runner=fake_run)
        self.assertEqual(len(seen), 3)
        self.assertIn("--host", seen[1])
        self.assertIn("ssh://deploy@host.example", seen[2])
        self.assertTrue(any("OpenSSH" in result for result in results))

    def test_doctor_reports_engine_failure(self):
        def fake_run(command, **kwargs):
            return type("Result", (), {"returncode": 1, "stdout": "", "stderr": "connection refused"})()

        with patch("dockrail.engine.docker_binary", return_value="/fake/docker"):
            with self.assertRaisesRegex(EngineError, "connection refused"):
                doctor(runner=fake_run)


if __name__ == "__main__":
    unittest.main()
