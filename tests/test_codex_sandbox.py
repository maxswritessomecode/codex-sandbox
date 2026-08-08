import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "codex_sandbox.py"


def run_cli(tmp_path: Path, *args):
    env = os.environ.copy()
    env["CODEX_SANDBOX_ROOT"] = str(tmp_path / "sandboxes")
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        check=True,
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


if __name__ == "__main__":
    unittest.main()
