import json
import os
import tempfile
import unittest
from pathlib import Path

from dockrail.config import read_config, validate_endpoint, validate_name, write_config


class ConfigTests(unittest.TestCase):
    def test_valid_endpoints(self):
        for endpoint in ("server", "deploy@server.example.com", "root@192.0.2.8:2222", "prod-vps"):
            self.assertEqual(validate_endpoint(endpoint), endpoint)

    def test_rejects_injection_and_invalid_ports(self):
        for endpoint in ("--host=bad", "user@host;rm", "user@host x", "user@host:70000", "a@b@c", "bad host"):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                validate_endpoint(endpoint)

    def test_name_is_limited(self):
        self.assertEqual(validate_name("test-prod_2"), "test-prod_2")
        with self.assertRaises(ValueError):
            validate_name("../bad")

    def test_round_trip_and_private_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dockrail" / "config.json"
            expected = {"version": 1, "targets": {"prod": "deploy@server.example.com"}}
            write_config(expected, path)
            self.assertEqual(read_config(path), expected)
            if os.name != "nt":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_invalid_config_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"version": 1, "targets": {"prod": "--help"}}))
            with self.assertRaises(ValueError):
                read_config(path)


if __name__ == "__main__":
    unittest.main()
