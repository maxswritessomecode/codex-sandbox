#!/usr/bin/env python3
"""Create and run isolated Codex workspaces."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_ROOT = Path.home() / "codex-sandboxes"
VERSION = "0.1.0"


def sandbox_root() -> Path:
    return Path(os.environ.get("CODEX_SANDBOX_ROOT", DEFAULT_ROOT)).expanduser()


def load_registry(root: Path) -> dict[str, dict[str, str]]:
    registry_path = root / "registry.json"
    if not registry_path.exists():
        return {}
    try:
        with registry_path.open("r", encoding="utf-8") as registry_file:
            return json.load(registry_file)
    except json.JSONDecodeError as error:
        raise SystemExit(f"Registry is not valid JSON: {registry_path} ({error})") from error


def save_registry(root: Path, registry: dict[str, dict[str, str]]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    registry_path = root / "registry.json"
    temp_path = registry_path.with_suffix(".json.tmp")
    with temp_path.open("w", encoding="utf-8") as registry_file:
        json.dump(registry, registry_file, indent=2, sort_keys=True)
        registry_file.write("\n")
    temp_path.replace(registry_path)


def validate_name(name: str) -> None:
    valid = name.replace("-", "").replace("_", "").isalnum()
    if not valid:
        raise SystemExit("Sandbox names may contain only letters, numbers, hyphens, and underscores.")


def init_sandbox(args: argparse.Namespace) -> int:
    validate_name(args.name)
    root = sandbox_root()
    sandbox = root / args.name
    config = sandbox / "config"
    workspace = sandbox / "workspace"

    if sandbox.exists() and not args.reuse:
        raise SystemExit(f"Sandbox already exists: {sandbox}. Use --reuse to keep existing files.")

    config.mkdir(parents=True, exist_ok=True)
    workspace.mkdir(parents=True, exist_ok=True)

    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    meta = {
        "name": args.name,
        "purpose": args.purpose,
        "created": created,
        "tool": "codex",
    }

    with (sandbox / "meta.json").open("w", encoding="utf-8") as meta_file:
        json.dump(meta, meta_file, indent=2)
        meta_file.write("\n")

    config_toml = config / "config.toml"
    if not config_toml.exists():
        config_toml.write_text(
            f'[projects."{workspace}"]\ntrust_level = "trusted"\n',
            encoding="utf-8",
        )

    registry = load_registry(root)
    registry[args.name] = {
        "purpose": args.purpose,
        "created": created,
        "tool": "codex",
        "notes": args.notes,
    }
    save_registry(root, registry)

    print(sandbox)
    return 0


def list_sandboxes(_: argparse.Namespace) -> int:
    registry = load_registry(sandbox_root())
    if not registry:
        return 0
    for name, meta in sorted(registry.items()):
        purpose = meta.get("purpose", "")
        print(f"{name}\t{purpose}")
    return 0


def sandbox_path(args: argparse.Namespace) -> int:
    validate_name(args.name)
    print(sandbox_root() / args.name)
    return 0


def run_codex(args: argparse.Namespace) -> int:
    validate_name(args.name)
    sandbox = sandbox_root() / args.name
    config = sandbox / "config"
    workspace = sandbox / "workspace"
    if not sandbox.exists():
        raise SystemExit(f"Sandbox does not exist: {sandbox}")
    if not config.is_dir():
        raise SystemExit(f"Sandbox config directory is missing: {config}. Recreate the sandbox with init.")
    if not workspace.is_dir():
        raise SystemExit(f"Sandbox workspace directory is missing: {workspace}. Recreate the sandbox with init.")

    command = args.command or ["codex"]
    env = os.environ.copy()
    env["CODEX_HOME"] = str(config)
    try:
        return subprocess.call(command, cwd=workspace, env=env)
    except FileNotFoundError:
        raise SystemExit(f"Command not found: {command[0]}") from None


def doctor(_: argparse.Namespace) -> int:
    root = sandbox_root()
    codex_path = shutil.which("codex")

    print(f"codex-sandbox {VERSION}")
    print(f"sandbox root: {root}")
    print(f"codex cli: {codex_path or 'not found on PATH'}")
    print("note: TCP ports are shared with your host and other sandboxes.")

    return 0 if codex_path else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-sandbox",
        description="Create and run isolated Codex workspaces.",
    )
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    init_parser = subparsers.add_parser("init", help="create a sandbox")
    init_parser.add_argument("name", help="sandbox name, such as demo or plugin-test")
    init_parser.add_argument("--purpose", default="Codex sandbox", help="short description stored in metadata")
    init_parser.add_argument("--notes", default="", help="optional notes stored in the registry")
    init_parser.add_argument("--reuse", action="store_true", help="reuse an existing sandbox directory")
    init_parser.set_defaults(func=init_sandbox)

    list_parser = subparsers.add_parser("list", help="list sandboxes")
    list_parser.set_defaults(func=list_sandboxes)

    path_parser = subparsers.add_parser("path", help="print a sandbox path")
    path_parser.add_argument("name", help="sandbox name")
    path_parser.set_defaults(func=sandbox_path)

    run_parser = subparsers.add_parser("run", help="run a command inside a sandbox workspace")
    run_parser.add_argument("name", help="sandbox name")
    run_parser.add_argument("command", nargs=argparse.REMAINDER, help="command to run; defaults to codex")
    run_parser.set_defaults(func=run_codex)

    doctor_parser = subparsers.add_parser("doctor", help="check the local Codex Sandbox setup")
    doctor_parser.set_defaults(func=doctor)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
