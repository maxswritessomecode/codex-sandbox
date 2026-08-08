import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "codex_sandbox.py"


def run_cli(tmp_path: Path, *args, extra_env=None):
    env = os.environ.copy()
    env["CODEX_SANDBOX_ROOT"] = str(tmp_path / "sandboxes")
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def run_cli_unchecked(tmp_path: Path, *args, extra_env=None):
    env = os.environ.copy()
    env["CODEX_SANDBOX_ROOT"] = str(tmp_path / "sandboxes")
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        env=env,
    )


class CodexSandboxTests(unittest.TestCase):
    def test_init_creates_sandbox_and_registry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            result = run_cli(tmp_path, "init", "codex-sandbox", "--purpose", "Test workspace")

            sandbox = tmp_path / "sandboxes" / "codex-sandbox"
            self.assertEqual(result.stdout.strip(), str(sandbox))
            self.assertTrue((sandbox / "config" / "config.toml").exists())
            self.assertTrue((sandbox / "workspace").is_dir())

            meta = json.loads((sandbox / "meta.json").read_text())
            self.assertEqual(meta["name"], "codex-sandbox")
            self.assertEqual(meta["purpose"], "Test workspace")

            registry = json.loads((tmp_path / "sandboxes" / "registry.json").read_text())
            self.assertEqual(registry["codex-sandbox"]["purpose"], "Test workspace")

    def test_list_outputs_registered_sandboxes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cli(tmp_path, "init", "one", "--purpose", "First")
            result = run_cli(tmp_path, "list")

            self.assertIn("one\tFirst", result.stdout)

    def test_path_outputs_sandbox_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            result = run_cli(tmp_path, "path", "demo")

            self.assertEqual(result.stdout.strip(), str(tmp_path / "sandboxes" / "demo"))

    def test_invalid_name_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_cli_unchecked(Path(temp_dir), "init", "../bad")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Sandbox names may contain only", result.stderr)

    def test_duplicate_init_requires_reuse(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cli(tmp_path, "init", "demo")
            result = run_cli_unchecked(tmp_path, "init", "demo")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Use --reuse", result.stderr)

    def test_reuse_existing_sandbox(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cli(tmp_path, "init", "demo", "--purpose", "First")
            run_cli(tmp_path, "init", "demo", "--purpose", "Second", "--reuse")

            registry = json.loads((tmp_path / "sandboxes" / "registry.json").read_text())
            self.assertEqual(registry["demo"]["purpose"], "Second")

    def test_run_custom_command_sets_codex_home_and_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cli(tmp_path, "init", "demo")
            result = run_cli(
                tmp_path,
                "run",
                "demo",
                sys.executable,
                "-c",
                "import os; print(os.environ['CODEX_HOME']); print(os.getcwd())",
            )

            lines = result.stdout.strip().splitlines()
            self.assertEqual(lines[0], str(tmp_path / "sandboxes" / "demo" / "config"))
            self.assertEqual(
                Path(lines[1]).resolve(),
                (tmp_path / "sandboxes" / "demo" / "workspace").resolve(),
            )

    def test_run_missing_command_has_clear_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cli(tmp_path, "init", "demo")
            result = run_cli_unchecked(tmp_path, "run", "demo", "definitely-not-a-command")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Command not found: definitely-not-a-command", result.stderr)

    def test_run_missing_workspace_has_clear_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cli(tmp_path, "init", "demo")
            (tmp_path / "sandboxes" / "demo" / "workspace").rmdir()
            result = run_cli_unchecked(tmp_path, "run", "demo", "env")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Sandbox workspace directory is missing", result.stderr)

    def test_corrupt_registry_has_clear_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            root = tmp_path / "sandboxes"
            root.mkdir()
            (root / "registry.json").write_text("{broken", encoding="utf-8")
            result = run_cli_unchecked(tmp_path, "list")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Registry is not valid JSON", result.stderr)

    def test_doctor_reports_missing_codex(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_cli_unchecked(Path(temp_dir), "doctor", extra_env={"PATH": ""})

            self.assertEqual(result.returncode, 1)
            self.assertIn("codex cli: not found on PATH", result.stdout)
            self.assertIn("TCP ports are shared", result.stdout)


if __name__ == "__main__":
    unittest.main()
