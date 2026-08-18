import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from agent_profile import redact_config_line


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "agent_profile.py"


def run_cli(tmp_path: Path, *args, extra_env=None):
    env = os.environ.copy()
    env["AGENT_PROFILE_ROOT"] = str(tmp_path / "sandboxes")
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )


def run_cli_unchecked(tmp_path: Path, *args, extra_env=None):
    env = os.environ.copy()
    env["AGENT_PROFILE_ROOT"] = str(tmp_path / "sandboxes")
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )


class CodexSandboxTests(unittest.TestCase):
    def test_init_creates_sandbox_and_registry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            result = run_cli(tmp_path, "init", "agent-profile", "--purpose", "Test workspace")

            sandbox = tmp_path / "sandboxes" / "agent-profile"
            self.assertEqual(result.stdout.strip(), str(sandbox.resolve()))
            self.assertTrue((sandbox / "config" / "config.toml").exists())
            self.assertTrue((sandbox / "workspace").is_dir())

            meta = json.loads((sandbox / "meta.json").read_text())
            self.assertEqual(meta["name"], "agent-profile")
            self.assertEqual(meta["purpose"], "Test workspace")

            registry = json.loads((tmp_path / "sandboxes" / "registry.json").read_text())
            self.assertEqual(registry["agent-profile"]["purpose"], "Test workspace")

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

            self.assertEqual(result.stdout.strip(), str((tmp_path / "sandboxes" / "demo").resolve()))

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
            self.assertEqual(lines[0], str((tmp_path / "sandboxes" / "demo" / "config").resolve()))
            self.assertEqual(
                Path(lines[1]).resolve(),
                (tmp_path / "sandboxes" / "demo" / "workspace").resolve(),
            )

    def test_claude_profile_uses_claude_config_dir_and_settings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cli(tmp_path, "init", "claude", "--tool", "claude")
            profile = tmp_path / "sandboxes" / "claude"
            self.assertTrue((profile / "config" / "settings.json").exists())
            self.assertFalse((profile / "config" / "config.toml").exists())
            result = run_cli(
                tmp_path,
                "run",
                "claude",
                "--clean-env",
                sys.executable,
                "-c",
                "import os; print(os.environ['CLAUDE_CONFIG_DIR']); print(os.environ.get('CODEX_HOME', '<missing>'))",
            )
            lines = result.stdout.strip().splitlines()
            self.assertEqual(lines[0], str((profile / "config").resolve()))
            self.assertEqual(lines[1], "<missing>")

    def test_claude_profile_defaults_to_claude_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cli(tmp_path, "init", "claude", "--tool", "claude")
            result = run_cli_unchecked(tmp_path, "run", "claude", extra_env={"PATH": "/nonexistent"})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Command not found: claude", result.stderr)

    def test_clean_environment_excludes_unlisted_variables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cli(tmp_path, "init", "demo")
            result = run_cli(
                tmp_path,
                "run",
                "demo",
                "--clean-env",
                sys.executable,
                "-c",
                "import os; print(os.environ.get('SANDBOX_TEST_SECRET', '<missing>')); print(os.environ['CODEX_HOME']); print(os.environ['PWD'])",
                extra_env={"SANDBOX_TEST_SECRET": "should-not-pass"},
            )

            lines = result.stdout.strip().splitlines()
            self.assertEqual(lines[0], "<missing>")
            self.assertEqual(lines[1], str((tmp_path / "sandboxes" / "demo" / "config").resolve()))
            self.assertEqual(lines[2], str((tmp_path / "sandboxes" / "demo" / "workspace").resolve()))

    def test_clean_environment_accepts_explicit_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cli(tmp_path, "init", "demo")
            result = run_cli(
                tmp_path,
                "run",
                "demo",
                "--clean-env",
                "--env",
                "SANDBOX_TEST_VALUE=explicit",
                sys.executable,
                "-c",
                "import os; print(os.environ['SANDBOX_TEST_VALUE'])",
            )

            self.assertEqual(result.stdout.strip(), "explicit")

    def test_environment_override_rejects_reserved_variables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cli(tmp_path, "init", "demo")
            result = run_cli_unchecked(tmp_path, "run", "demo", "--env", "CODEX_HOME=/tmp/wrong", "env")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot replace reserved variable", result.stderr)

    def test_clone_excludes_runtime_state_and_creates_empty_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cli(tmp_path, "init", "source", "--purpose", "Source sandbox")
            source = tmp_path / "sandboxes" / "source"
            (source / "config" / "skills").mkdir()
            (source / "config" / "skills" / "example.md").write_text("skill", encoding="utf-8")
            (source / "config" / "auth.json").write_text("secret", encoding="utf-8")
            (source / "config" / "history.jsonl").write_text("private", encoding="utf-8")

            run_cli(tmp_path, "clone", "source", "clone")
            clone = tmp_path / "sandboxes" / "clone"
            self.assertTrue((clone / "config" / "skills" / "example.md").exists())
            self.assertFalse((clone / "config" / "auth.json").exists())
            self.assertFalse((clone / "config" / "history.jsonl").exists())
            self.assertEqual(list((clone / "workspace").iterdir()), [])
            self.assertIn(str(clone / "workspace"), (clone / "config" / "config.toml").read_text())
            self.assertNotIn(str(source / "workspace"), (clone / "config" / "config.toml").read_text())

    def test_export_excludes_runtime_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cli(tmp_path, "init", "demo")
            config = tmp_path / "sandboxes" / "demo" / "config"
            (config / "auth.json").write_text("secret", encoding="utf-8")
            (config / "skills").mkdir()
            (config / "skills" / "example.md").write_text("skill", encoding="utf-8")
            archive_path = tmp_path / "demo.tar.gz"

            run_cli(tmp_path, "export", "demo", "--output", str(archive_path))
            with tarfile.open(archive_path, "r:gz") as archive:
                names = archive.getnames()
            self.assertIn("demo/meta.json", names)
            self.assertIn("demo/config/skills/example.md", names)
            self.assertNotIn("demo/config/auth.json", names)

    def test_reset_requires_confirmation_and_recreates_sandbox(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cli(tmp_path, "init", "demo", "--purpose", "Keep this purpose")
            sandbox = tmp_path / "sandboxes" / "demo"
            (sandbox / "workspace" / "old.txt").write_text("old", encoding="utf-8")

            result = run_cli_unchecked(tmp_path, "reset", "demo")
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue((sandbox / "workspace" / "old.txt").exists())

            run_cli(tmp_path, "reset", "demo", "--yes")
            self.assertFalse((sandbox / "workspace" / "old.txt").exists())
            registry = json.loads((tmp_path / "sandboxes" / "registry.json").read_text())
            self.assertEqual(registry["demo"]["purpose"], "Keep this purpose")

    def test_diff_redacts_sensitive_config_lines(self):
        self.assertEqual(redact_config_line('api_key = "secret-value"\n'), 'api_key = <redacted>\n')
        self.assertEqual(redact_config_line('model = "gpt-5"\n'), 'model = "gpt-5"\n')

    def test_relative_sandbox_root_is_absolute_in_child(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            relative_root = Path("relative-sandboxes")
            run_cli(tmp_path, "init", "demo", extra_env={"AGENT_PROFILE_ROOT": str(relative_root)})
            result = run_cli(
                tmp_path,
                "run",
                "demo",
                sys.executable,
                "-c",
                "import os; print(os.environ['CODEX_HOME'])",
                extra_env={"AGENT_PROFILE_ROOT": str(relative_root)},
            )

            self.assertTrue(Path(result.stdout.strip()).is_absolute())

    def test_config_path_is_toml_escaped(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            root = tmp_path / 'root"with-quote'
            run_cli(tmp_path, "init", "demo", extra_env={"AGENT_PROFILE_ROOT": str(root)})

            config = (root / "demo" / "config" / "config.toml").read_text()
            self.assertIn(
                'projects."' + str((root / "demo" / "workspace").resolve()).replace('"', '\\"') + '"',
                config,
            )

    def test_registry_wrong_json_shape_has_clear_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            root = tmp_path / "sandboxes"
            root.mkdir()
            (root / "registry.json").write_text("[]", encoding="utf-8")
            result = run_cli_unchecked(tmp_path, "list")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Registry must contain a JSON object", result.stderr)

    def test_created_state_uses_private_directory_and_file_modes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cli(tmp_path, "init", "demo")
            root = tmp_path / "sandboxes"
            sandbox = root / "demo"

            self.assertEqual(root.stat().st_mode & 0o777, 0o700)
            self.assertEqual(sandbox.stat().st_mode & 0o777, 0o700)
            self.assertEqual((sandbox / "config").stat().st_mode & 0o777, 0o700)
            self.assertEqual((sandbox / "workspace").stat().st_mode & 0o777, 0o700)
            self.assertEqual((root / "registry.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual((sandbox / "meta.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual((sandbox / "config" / "config.toml").stat().st_mode & 0o777, 0o600)

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
