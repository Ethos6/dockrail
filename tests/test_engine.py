import unittest
from pathlib import Path

from dockrail.engine import compose_command


class EngineCommandTests(unittest.TestCase):
    def test_local_deploy_never_adds_remote_host(self):
        command = compose_command("up", project="demo", compose_file="compose.yaml", build=True)
        self.assertEqual(command[0], "docker")
        self.assertNotIn("--host", command)
        self.assertEqual(command[-3:], ["up", "--detach", "--build"])

    def test_remote_deploy_uses_ssh_and_no_shell(self):
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


if __name__ == "__main__":
    unittest.main()
