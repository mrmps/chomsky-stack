#!/usr/bin/env python3

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "skills" / "junk-detection" / "scripts" / "scan_hotspots.py"
SCANNER_SPEC = importlib.util.spec_from_file_location("junk_detection_scanner", SCANNER)
if SCANNER_SPEC is None or SCANNER_SPEC.loader is None:
    raise RuntimeError("could not load junk-detection scanner")
SCANNER_MODULE = importlib.util.module_from_spec(SCANNER_SPEC)
SCANNER_SPEC.loader.exec_module(SCANNER_MODULE)


def run_scanner(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCANNER), str(repository), *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


class JunkDetectionScannerTest(unittest.TestCase):
    def make_repository(self, parent: Path) -> Path:
        repository = parent / "repository"
        repository.mkdir()
        subprocess.run(["git", "init", "-q", str(repository)], check=True)
        return repository

    def test_symlink_outside_repository_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = self.make_repository(root)
            secret = root / "secret.py"
            secret.write_text("TODO PRIVATE-SENTINEL\n", encoding="utf-8")
            os.symlink(secret, repository / "leak.py")

            result = run_scanner(repository, "--scope", "all", "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["file_count"], 0)
            self.assertNotIn("PRIVATE-SENTINEL", result.stdout)

    def test_terminal_controls_are_escaped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = self.make_repository(root)
            (repository / "escape.py").write_text(
                "TODO \x1b]52;c;Y2xpcGJvYXJk\x07\n",
                encoding="utf-8",
            )

            result = run_scanner(repository, "--scope", "all")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("\x1b", result.stdout)
            self.assertNotIn("\x07", result.stdout)
            self.assertIn("\\x1b]52;c;Y2xpcGJvYXJk\\x07", result.stdout)

    def test_newline_in_filename_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = self.make_repository(root)
            filename = "strange\nname.py"
            (repository / filename).write_text("TODO check me\n", encoding="utf-8")

            result = run_scanner(repository, "--scope", "all", "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["file_count"], 1)
            self.assertEqual(report["metrics"][0]["path"], filename)
            self.assertEqual(report["markers"]["stub"][0]["path"], filename)

    def test_invalid_utf8_filename_does_not_crash_scan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = self.make_repository(root)
            filename = b"invalid-\xff.py"
            path = os.path.join(os.fsencode(repository), filename)
            try:
                descriptor = os.open(path, os.O_CREAT | os.O_WRONLY, 0o600)
            except OSError as error:
                self.skipTest("filesystem rejects invalid UTF-8 filenames: {}".format(error))
            try:
                os.write(descriptor, b"TODO check me\n")
            finally:
                os.close(descriptor)

            result = run_scanner(repository, "--scope", "all", "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["file_count"], 1)
            self.assertEqual(os.fsencode(report["metrics"][0]["path"]), filename)

    def test_git_output_decoding_preserves_invalid_bytes(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["git"],
            returncode=0,
            stdout=b"invalid-\xff.py\0",
            stderr=b"",
        )
        with mock.patch.object(SCANNER_MODULE.subprocess, "run", return_value=completed):
            records = SCANNER_MODULE.run_git(
                Path("."),
                ["ls-files", "-z"],
                nul_terminated=True,
            )

        self.assertEqual(len(records), 1)
        self.assertEqual(os.fsencode(records[0]), b"invalid-\xff.py")

    def test_non_repository_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_scanner(Path(directory), "--scope", "diff")

            self.assertEqual(result.returncode, 2)
            self.assertIn("not a git repository root", result.stderr)


if __name__ == "__main__":
    unittest.main()
