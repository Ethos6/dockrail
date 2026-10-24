import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dockrail import cli
from dockrail.engine import EngineError


class FakeResult:
    returncode = 0


class CliTests(unittest.TestCase):
    def test_init_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "compose.yaml"
            path.write_text("keep me")
            with patch("sys.stdout"), patch("sys.stderr"):
                code = cli.main(["init", directory])
            self.assertEqual(code, 2)
            self.assertEqual(path.read_text(), "keep me")

    def test_init_creates_loopback_example(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("sys.stdout"):
                code = cli.main(["init", directory])
            self.assertEqual(code, 0)
            self.assertIn('127.0.0.1:8080:80', (Path(directory) / "compose.yaml").read_text())

    def test_deploy_invokes_fake_docker_as_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "compose.yaml").write_text("services: {}\n")
            seen = {}

            def fake_run(command, **kwargs):
                seen["command"] = command
                seen.update(kwargs)
                return FakeResult()

            with patch("sys.stdout"), patch("sys.stderr"), patch("dockrail.engine.docker_binary", return_value="/fake/docker"), patch("dockrail.engine.subprocess.run", side_effect=fake_run), patch("pathlib.Path.cwd", return_value=Path(directory)):
                code = cli.main(["deploy", "--project", "safe-project"])
            self.assertEqual(code, 0)
            self.assertEqual(seen["command"][0], "/fake/docker")
            self.assertIn("up", seen["command"])
            self.assertEqual(seen["shell"] if "shell" in seen else None, None)
            self.assertEqual(seen["cwd"], directory)

    def test_missing_compose_file_is_reported_without_engine_call(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("sys.stdout"), patch("sys.stderr"), patch("pathlib.Path.cwd", return_value=Path(directory)):
                code = cli.main(["deploy"])
            self.assertEqual(code, 2)

    def test_project_name_cannot_inject_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "compose.yaml").write_text("services: {}\n")
            with patch("sys.stdout"), patch("sys.stderr"), patch("pathlib.Path.cwd", return_value=Path(directory)):
                code = cli.main(["status", "--project", "ok;--volumes"])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
