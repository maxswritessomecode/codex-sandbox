#!/usr/bin/env python3
"""Create and run named configuration profiles for coding agents."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import difflib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path
import re

import fcntl


DEFAULT_ROOT = Path.home() / "agent-profiles"
VERSION = "0.3.0"
TOOLS = {
    "codex": {"executable": "codex", "env_key": "CODEX_HOME", "home": ".codex", "default_purpose": "Codex profile"},
    "claude": {"executable": "claude", "env_key": "CLAUDE_CONFIG_DIR", "home": ".claude", "default_purpose": "Claude Code profile"},
}
ENV_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CLEAN_ENV_KEYS = {
    "COLORTERM",
    "HOME",
    "LANG",
    "LOGNAME",
    "PATH",
    "SHELL",
    "TERM",
    "TMPDIR",
    "USER",
}
RESERVED_ENV_KEYS = {"CODEX_HOME", "CLAUDE_CONFIG_DIR", "HOME", "PWD"}
RUNTIME_ENTRY_NAMES = {
    "auth.json",
    ".credentials.json",
    ".claude.json",
    "history.jsonl",
    "installation_id",
    "models_cache.json",
    "sessions",
    "logs",
    ".tmp",
    "thread-writer-locks",
    "shell_snapshots",
    "generated_images",
    "attachments",
    "process_manager",
    "mcp-oauth-locks",
    "statsig",
    "file-history",
    "paste-cache",
    "todos",
    "tasks",
    "debug",
}
SENSITIVE_CONFIG_LINE = re.compile(r"(token|secret|password|api[_-]?key)", re.IGNORECASE)


def sandbox_root() -> Path:
    configured_root = os.environ.get("AGENT_PROFILE_ROOT", os.environ.get("CODEX_SANDBOX_ROOT", DEFAULT_ROOT))
    return Path(configured_root).expanduser().resolve()


def tool_definition(tool: str) -> dict[str, str]:
    try:
        return TOOLS[tool]
    except KeyError:
        choices = ", ".join(sorted(TOOLS))
        raise SystemExit(f"Unknown agent tool {tool!r}. Choose from: {choices}.") from None


def sandbox_tool(name: str) -> str:
    metadata_path = sandbox_root() / name / "meta.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise SystemExit(f"Sandbox metadata is missing or invalid: {metadata_path}") from error
    return metadata.get("tool", "codex")


def ensure_private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)


def ensure_not_symlink(path: Path, description: str) -> None:
    if path.is_symlink():
        raise SystemExit(f"Sandbox {description} must not be a symlink: {path}")


def write_private_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)


def validate_registry(registry: object, registry_path: Path) -> dict[str, dict[str, str]]:
    if not isinstance(registry, dict):
        raise SystemExit(f"Registry must contain a JSON object: {registry_path}")
    for name, metadata in registry.items():
        if not isinstance(name, str) or not name:
            raise SystemExit(f"Registry contains an invalid sandbox name: {registry_path}")
        validate_name(name)
        if not isinstance(metadata, dict):
            raise SystemExit(f"Registry entry is not an object: {registry_path} ({name})")
        for key, value in metadata.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise SystemExit(f"Registry entry contains a non-string field: {registry_path} ({name})")
    return registry


@contextmanager
def registry_lock(root: Path):
    ensure_private_directory(root)
    lock_path = root / ".registry.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        lock_path.chmod(0o600)
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def load_registry(root: Path) -> dict[str, dict[str, str]]:
    registry_path = root / "registry.json"
    if not registry_path.exists():
        return {}
    try:
        with registry_path.open("r", encoding="utf-8") as registry_file:
            return validate_registry(json.load(registry_file), registry_path)
    except json.JSONDecodeError as error:
        raise SystemExit(f"Registry is not valid JSON: {registry_path} ({error})") from error


def save_registry_unlocked(root: Path, registry: dict[str, dict[str, str]]) -> None:
    registry_path = root / "registry.json"
    validate_registry(registry, registry_path)
    temp_path = root / f".{registry_path.name}.{os.getpid()}.tmp"
    with temp_path.open("w", encoding="utf-8") as registry_file:
        json.dump(registry, registry_file, indent=2, sort_keys=True)
        registry_file.write("\n")
        registry_file.flush()
        os.fsync(registry_file.fileno())
    temp_path.chmod(0o600)
    temp_path.replace(registry_path)


def save_registry(root: Path, registry: dict[str, dict[str, str]]) -> None:
    ensure_private_directory(root)
    with registry_lock(root):
        save_registry_unlocked(root, registry)


def validate_name(name: str) -> None:
    valid = name.replace("-", "").replace("_", "").isalnum()
    if not valid:
        raise SystemExit("Sandbox names may contain only letters, numbers, hyphens, and underscores.")


def parse_extra_environment(values: list[str]) -> dict[str, str]:
    extra: dict[str, str] = {}
    for value in values:
        key, separator, env_value = value.partition("=")
        if not separator or not ENV_NAME_PATTERN.fullmatch(key):
            raise SystemExit(f"Environment overrides must use NAME=VALUE syntax: {value}")
        if key in RESERVED_ENV_KEYS:
            raise SystemExit(f"Environment override cannot replace reserved variable: {key}")
        extra[key] = env_value
    return extra


def build_environment(args: argparse.Namespace, config: Path, workspace: Path, tool: str) -> dict[str, str]:
    if args.clean_env:
        env = {
            key: value
            for key, value in os.environ.items()
            if key in CLEAN_ENV_KEYS or key.startswith("LC_")
        }
        env.setdefault("PATH", os.defpath)
        env.setdefault("HOME", str(Path.home()))
    else:
        env = os.environ.copy()

    env.update(parse_extra_environment(args.env))
    env[tool_definition(tool)["env_key"]] = str(config)
    env["PWD"] = str(workspace)
    return env


def permission_warning(path: Path) -> str | None:
    try:
        mode = path.stat().st_mode & 0o777
    except OSError as error:
        return f"unreadable ({error})"
    if mode & 0o077:
        return f"permissions {mode:04o} are broader than owner-only"
    return None


def is_runtime_entry(name: str) -> bool:
    return (
        name in RUNTIME_ENTRY_NAMES
        or name.endswith((".sqlite", ".sqlite-shm", ".sqlite-wal"))
        or name.endswith((".log", ".jsonl"))
    )


def ignore_runtime_entries(_: str, names: list[str]) -> set[str]:
    return {name for name in names if is_runtime_entry(name)}


def ensure_tree_has_no_symlinks(path: Path) -> None:
    for entry in path.rglob("*"):
        if entry.is_symlink():
            raise SystemExit(f"Lifecycle operation does not support symlinks: {entry}")


def get_sandbox(name: str) -> tuple[Path, Path, Path]:
    validate_name(name)
    sandbox = sandbox_root() / name
    return sandbox, sandbox / "config", sandbox / "workspace"


def require_sandbox(name: str) -> tuple[Path, Path, Path]:
    sandbox, config, workspace = get_sandbox(name)
    if not sandbox.is_dir() or sandbox.is_symlink():
        raise SystemExit(f"Sandbox does not exist or is unsafe: {sandbox}")
    if not config.is_dir() or config.is_symlink():
        raise SystemExit(f"Sandbox config directory is missing or unsafe: {config}")
    if not workspace.is_dir() or workspace.is_symlink():
        raise SystemExit(f"Sandbox workspace directory is missing or unsafe: {workspace}")
    return sandbox, config, workspace


def registry_entry(name: str) -> dict[str, str]:
    root = sandbox_root()
    with registry_lock(root):
        registry = load_registry(root)
    if name not in registry:
        raise SystemExit(f"Sandbox is not registered: {name}")
    return registry[name]


def update_registry(name: str, metadata: dict[str, str] | None = None, *, remove: bool = False) -> None:
    root = sandbox_root()
    with registry_lock(root):
        registry = load_registry(root)
        if remove:
            registry.pop(name, None)
        else:
            registry[name] = metadata or {}
        save_registry_unlocked(root, registry)


def init_sandbox(args: argparse.Namespace) -> int:
    validate_name(args.name)
    profile = tool_definition(args.tool)
    purpose = args.purpose or profile["default_purpose"]
    root = sandbox_root()
    sandbox = root / args.name
    config = sandbox / "config"
    workspace = sandbox / "workspace"

    if sandbox.exists() and not args.reuse:
        raise SystemExit(f"Sandbox already exists: {sandbox}. Use --reuse to keep existing files.")

    ensure_private_directory(root)
    ensure_not_symlink(sandbox, "directory")
    ensure_private_directory(sandbox)
    ensure_not_symlink(config, "config directory")
    ensure_not_symlink(workspace, "workspace directory")
    ensure_private_directory(config)
    ensure_private_directory(workspace)

    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    meta = {
        "name": args.name,
        "purpose": purpose,
        "created": created,
        "tool": args.tool,
    }

    write_private_text(sandbox / "meta.json", json.dumps(meta, indent=2) + "\n")

    config_toml = config / "config.toml"
    claude_settings = config / "settings.json"
    if args.tool == "codex" and not config_toml.exists():
        write_private_text(
            config_toml,
            f"[projects.{json.dumps(str(workspace))}]\ntrust_level = \"trusted\"\n",
        )
    elif config_toml.exists():
        config_toml.chmod(0o600)
    if args.tool == "claude" and not claude_settings.exists():
        write_private_text(claude_settings, "{}\n")

    with registry_lock(root):
        registry = load_registry(root)
        registry[args.name] = {
            "purpose": purpose,
            "created": created,
            "tool": args.tool,
            "notes": args.notes,
        }
        save_registry_unlocked(root, registry)

    print(sandbox)
    return 0


def list_sandboxes(_: argparse.Namespace) -> int:
    root = sandbox_root()
    with registry_lock(root):
        registry = load_registry(root)
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


def run_profile(args: argparse.Namespace) -> int:
    validate_name(args.name)
    sandbox = sandbox_root() / args.name
    config = sandbox / "config"
    workspace = sandbox / "workspace"
    if not sandbox.exists():
        raise SystemExit(f"Sandbox does not exist: {sandbox}")
    ensure_not_symlink(sandbox, "directory")
    if not config.is_dir():
        raise SystemExit(f"Sandbox config directory is missing: {config}. Recreate the sandbox with init.")
    ensure_not_symlink(config, "config directory")
    if not workspace.is_dir():
        raise SystemExit(f"Sandbox workspace directory is missing: {workspace}. Recreate the sandbox with init.")
    ensure_not_symlink(workspace, "workspace directory")

    tool = sandbox_tool(args.name)
    command = args.command or [tool_definition(tool)["executable"]]
    env = build_environment(args, config, workspace, tool)
    try:
        return subprocess.call(command, cwd=workspace, env=env)
    except FileNotFoundError:
        raise SystemExit(f"Command not found: {command[0]}") from None


def clone_sandbox(args: argparse.Namespace) -> int:
    source_sandbox, source_config, source_workspace = require_sandbox(args.source)
    validate_name(args.destination)
    if args.source == args.destination:
        raise SystemExit("Source and destination sandboxes must be different.")
    destination_sandbox, destination_config, destination_workspace = get_sandbox(args.destination)
    if destination_sandbox.exists() or destination_sandbox.is_symlink():
        raise SystemExit(f"Destination sandbox already exists: {destination_sandbox}")
    ensure_tree_has_no_symlinks(source_config)

    ensure_private_directory(sandbox_root())
    ensure_private_directory(destination_sandbox)
    ensure_private_directory(destination_config)
    ensure_private_directory(destination_workspace)
    shutil.copytree(source_config, destination_config, dirs_exist_ok=True, ignore=ignore_runtime_entries)
    for directory in (destination_sandbox, destination_config, destination_workspace):
        directory.chmod(0o700)
    source_meta = json.loads((source_sandbox / "meta.json").read_text(encoding="utf-8"))
    tool = source_meta.get("tool", "codex")
    tool_definition(tool)
    config_toml = destination_config / "config.toml"
    if tool == "codex" and not config_toml.exists():
        write_private_text(
            config_toml,
            f"[projects.{json.dumps(str(destination_workspace))}]\ntrust_level = \"trusted\"\n",
        )
    elif config_toml.exists():
        config_text = config_toml.read_text(encoding="utf-8")
        source_header = f"[projects.{json.dumps(str(source_workspace))}]"
        destination_header = f"[projects.{json.dumps(str(destination_workspace))}]"
        if source_header in config_text:
            write_private_text(config_toml, config_text.replace(source_header, destination_header, 1))
        config_toml.chmod(0o600)

    purpose = args.purpose if args.purpose is not None else f"Clone of {args.source}: {source_meta.get('purpose', tool_definition(tool)['default_purpose'])}"
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write_private_text(
        destination_sandbox / "meta.json",
        json.dumps({"name": args.destination, "purpose": purpose, "created": created, "tool": tool}, indent=2) + "\n",
    )
    update_registry(
        args.destination,
        {"purpose": purpose, "created": created, "tool": tool, "notes": args.notes},
    )
    print(destination_sandbox)
    return 0


def redact_config_line(line: str) -> str:
    if not SENSITIVE_CONFIG_LINE.search(line):
        return line
    key, separator, _ = line.partition("=")
    return f"{key}{separator} <redacted>\n" if separator else "<redacted line>\n"


def diff_sandbox(args: argparse.Namespace) -> int:
    _, config, _ = require_sandbox(args.name)
    tool = sandbox_tool(args.name)
    if tool == "claude":
        sandbox_config = config / "settings.json"
        main_config = Path.home() / ".claude" / "settings.json"
    else:
        sandbox_config = config / "config.toml"
        main_config = Path.home() / ".codex" / "config.toml"
    if not sandbox_config.exists():
        raise SystemExit(f"Sandbox config does not exist: {sandbox_config}")
    if not main_config.exists():
        raise SystemExit(f"Main {tool_definition(tool)['executable']} config does not exist: {main_config}")
    sandbox_lines = [redact_config_line(line) for line in sandbox_config.read_text(encoding="utf-8").splitlines(keepends=True)]
    main_lines = [redact_config_line(line) for line in main_config.read_text(encoding="utf-8").splitlines(keepends=True)]
    difference = list(difflib.unified_diff(main_lines, sandbox_lines, fromfile=str(main_config), tofile=str(sandbox_config)))
    if difference:
        sys.stdout.writelines(difference)
        return 1
    print(f"Configuration matches the main {tool_definition(tool)['executable']} config.")
    return 0


def reset_sandbox(args: argparse.Namespace) -> int:
    sandbox, _, _ = require_sandbox(args.name)
    if not args.yes:
        raise SystemExit(f"Reset is destructive. Re-run with --yes to delete and recreate: {sandbox}")
    metadata = registry_entry(args.name)
    shutil.rmtree(sandbox)
    update_registry(args.name, remove=True)
    init_args = argparse.Namespace(
        name=args.name,
        purpose=metadata.get("purpose", tool_definition(metadata.get("tool", "codex"))["default_purpose"]),
        notes=metadata.get("notes", ""),
        tool=metadata.get("tool", "codex"),
        reuse=False,
    )
    return init_sandbox(init_args)


def export_sandbox(args: argparse.Namespace) -> int:
    sandbox, config, _ = require_sandbox(args.name)
    ensure_tree_has_no_symlinks(config)
    output = Path(args.output).expanduser().resolve() if args.output else Path.cwd() / f"{args.name}-export.tar.gz"
    if output.exists():
        raise SystemExit(f"Export output already exists: {output}")
    try:
        output.relative_to(sandbox)
    except ValueError:
        pass
    else:
        raise SystemExit(f"Export output must be outside the sandbox: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as archive:
        archive.add(sandbox / "meta.json", arcname=f"{args.name}/meta.json")
        for path in sorted(config.rglob("*")):
            relative = path.relative_to(sandbox)
            if any(is_runtime_entry(part) for part in relative.parts):
                continue
            archive.add(path, arcname=f"{args.name}/{relative}", recursive=False)
    output.chmod(0o600)
    print(output)
    return 0


def doctor(_: argparse.Namespace) -> int:
    root = sandbox_root()
    tool_paths = {tool: shutil.which(profile["executable"]) for tool, profile in TOOLS.items()}
    problems = []

    print(f"agent-profile {VERSION}")
    print(f"profile root: {root}")
    for tool, path in tool_paths.items():
        print(f"{tool} cli: {path or 'not found on PATH'}")
    print("note: TCP ports are shared with your host and other sandboxes.")

    for tool, path in tool_paths.items():
        if not path:
            problems.append(f"{tool} executable not found")
        elif not os.access(path, os.X_OK):
            problems.append(f"{tool} executable is not executable")

    if not root.exists():
        print("sandbox root status: not created yet")
    elif not root.is_dir():
        print("sandbox root status: not a directory")
        problems.append("sandbox root is not a directory")
    else:
        root_warning = permission_warning(root)
        print(f"sandbox root status: writable={os.access(root, os.W_OK)}")
        if root_warning:
            print(f"sandbox root warning: {root_warning}")
        if not os.access(root, os.W_OK):
            problems.append("sandbox root is not writable")

        registry_path = root / "registry.json"
        if registry_path.exists():
            try:
                registry = load_registry(root)
            except SystemExit as error:
                print(f"registry status: {error}")
                problems.append("registry is invalid")
            else:
                registry_warning = permission_warning(registry_path)
                print(f"registry status: valid ({len(registry)} sandbox(s))")
                if registry_warning:
                    print(f"registry warning: {registry_warning}")

                for name in registry:
                    config_path = root / name / "config"
                    workspace_path = root / name / "workspace"
                    if not config_path.is_dir() or not workspace_path.is_dir():
                        print(f"sandbox warning: {name} is missing config or workspace")
                        problems.append(f"sandbox {name} is incomplete")
                        continue
                    for path in (config_path, workspace_path):
                        warning = permission_warning(path)
                        if warning:
                            print(f"sandbox warning: {name} {path.name}: {warning}")
                    try:
                        tool = sandbox_tool(name)
                    except SystemExit as error:
                        print(f"sandbox warning: {name}: {error}")
                        problems.append(f"sandbox {name} has invalid metadata")
                        continue
                    home = (Path.home() / tool_definition(tool)["home"]).resolve()
                    for config_file in config_path.glob("*"):
                        if config_file.is_file() and str(home) in config_file.read_text(encoding="utf-8", errors="replace"):
                            print(f"sandbox warning: {name} config references main {tool} home")
                            problems.append(f"sandbox {name} references main {tool} home")

    return 0 if not problems else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-profile",
        description="Create and run named configuration profiles for coding agents.",
    )
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    init_parser = subparsers.add_parser("init", help="create a profile")
    init_parser.add_argument("name", help="profile name, such as demo or plugin-test")
    init_parser.add_argument("--tool", choices=sorted(TOOLS), default="codex", help="agent CLI this profile is for")
    init_parser.add_argument("--purpose", default=None, help="short description stored in metadata")
    init_parser.add_argument("--notes", default="", help="optional notes stored in the registry")
    init_parser.add_argument("--reuse", action="store_true", help="reuse an existing profile directory")
    init_parser.set_defaults(func=init_sandbox)

    list_parser = subparsers.add_parser("list", help="list profiles")
    list_parser.set_defaults(func=list_sandboxes)

    path_parser = subparsers.add_parser("path", help="print a profile path")
    path_parser.add_argument("name", help="profile name")
    path_parser.set_defaults(func=sandbox_path)

    run_parser = subparsers.add_parser("run", help="run an agent or command inside a profile workspace")
    run_parser.add_argument("name", help="profile name")
    run_parser.add_argument(
        "--clean-env",
        action="store_true",
        help="run with a minimal environment instead of inheriting the shell environment",
    )
    run_parser.add_argument(
        "--env",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="explicitly add an environment variable (repeatable; used with or without --clean-env)",
    )
    run_parser.add_argument("command", nargs=argparse.REMAINDER, help="command to run; defaults to the profile's agent")
    run_parser.set_defaults(func=run_profile)

    clone_parser = subparsers.add_parser("clone", help="clone configuration into a new profile")
    clone_parser.add_argument("source", help="existing profile name")
    clone_parser.add_argument("destination", help="new profile name")
    clone_parser.add_argument("--purpose", default=None, help="purpose for the cloned sandbox")
    clone_parser.add_argument("--notes", default="", help="optional notes stored in the registry")
    clone_parser.set_defaults(func=clone_sandbox)

    diff_parser = subparsers.add_parser("diff", help="compare a profile config with the main agent config")
    diff_parser.add_argument("name", help="sandbox name")
    diff_parser.set_defaults(func=diff_sandbox)

    reset_parser = subparsers.add_parser("reset", help="delete and recreate a profile")
    reset_parser.add_argument("name", help="profile name")
    reset_parser.add_argument("--yes", action="store_true", help="confirm destructive reset")
    reset_parser.set_defaults(func=reset_sandbox)

    export_parser = subparsers.add_parser("export", help="export safe profile configuration")
    export_parser.add_argument("name", help="profile name")
    export_parser.add_argument("--output", help="archive path; defaults to NAME-export.tar.gz")
    export_parser.set_defaults(func=export_sandbox)

    doctor_parser = subparsers.add_parser("doctor", help="check the local agent-profile setup")
    doctor_parser.set_defaults(func=doctor)

    return parser


def normalize_run_arguments(argv: list[str]) -> list[str]:
    """Allow run options immediately after the sandbox name and before its command."""
    if len(argv) < 3 or argv[0] != "run":
        return argv

    name = argv[1]
    remainder = argv[2:]
    options: list[str] = []
    index = 0
    while index < len(remainder):
        value = remainder[index]
        if value == "--clean-env":
            options.append(value)
            index += 1
        elif value == "--env" and index + 1 < len(remainder):
            options.extend(remainder[index : index + 2])
            index += 2
        else:
            break
    return ["run", *options, name, *remainder[index:]]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args(normalize_run_arguments(sys.argv[1:]))
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
