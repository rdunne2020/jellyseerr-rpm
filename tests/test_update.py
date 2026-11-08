import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.util.spec_from_file_location("check_update", ROOT / "scripts/check-update.py")
updater = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(updater)
SPEC = "Name: seerr\nVersion:    3.5.0\nRelease:    4%{?dist}\n"


class UpdateTests(unittest.TestCase):
    def test_new_release_resets_release(self):
        result, version = updater.update_spec(SPEC, {"tag_name": "v3.10.0"})
        self.assertEqual(version, "3.10.0")
        self.assertIn("Version:    3.10.0", result)
        self.assertIn("Release:        1%{?dist}", result)
        self.assertIn("Name: seerr", result)

    def test_equal_or_older_release_is_noop(self):
        for tag in ("v3.5.0", "v3.4.9", "v2.99.0"):
            with self.subTest(tag=tag):
                self.assertEqual(updater.update_spec(SPEC, {"tag_name": tag}), (SPEC, None))

    def test_rejects_invalid_releases(self):
        for release in ({}, {"tag_name": "v3.6.0-rc.1"}, {"tag_name": "3.6.0"},
                        {"tag_name": "v3.6.0\n"}, {"tag_name": "v3.6.0", "draft": True},
                        {"tag_name": "v3.6.0", "prerelease": True}):
            with self.subTest(release=release), self.assertRaises(ValueError):
                updater.update_spec(SPEC, release)

    def test_rejects_missing_or_duplicate_fields(self):
        for spec in ("", SPEC + "Version: 3.5.0\n", SPEC.replace("Release:", "Other:")):
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                updater.update_spec(spec, {"tag_name": "v3.6.0"})

    def test_cli_and_idempotence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec, release, output = (root / name for name in ("seerr.spec", "release.json", "output"))
            spec.write_text(SPEC)
            release.write_text(json.dumps({"tag_name": "v3.6.0"}))
            command = ["python3", str(ROOT / "scripts/check-update.py"), "--spec", str(spec),
                       "--release-json", str(release)]
            env = {**os.environ, "GITHUB_OUTPUT": str(output)}
            subprocess.run(command, check=True, env=env, capture_output=True)
            self.assertEqual(output.read_text(), "version=3.6.0\n")
            first = spec.read_text()
            subprocess.run(command, check=True, env=env, capture_output=True)
            self.assertEqual(spec.read_text(), first)
            self.assertEqual(output.read_text(), "version=3.6.0\nversion=\n")

    def test_invalid_response_leaves_spec_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            spec, release = Path(directory) / "spec", Path(directory) / "release.json"
            spec.write_text(SPEC)
            release.write_text('{"tag_name":"invalid"}')
            result = subprocess.run(["python3", str(ROOT / "scripts/check-update.py"),
                                     "--spec", str(spec), "--release-json", str(release)],
                                    capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(spec.read_text(), SPEC)
