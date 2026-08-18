# Commands

`agent-profile` is a small Python CLI for creating named Codex or Claude Code configuration profiles and workspaces.

## Install Locally

Prerequisite: install and authenticate the Codex or Claude Code CLI first. Each profile uses a separate config directory (`CODEX_HOME` for Codex or `CLAUDE_CONFIG_DIR` for Claude Code).

Recommended:

```sh
pipx install git+https://github.com/maxswritessomecode/agent-profile.git
```

If you do not have `pipx`, install it first or use the local development/manual install path below.

For local development:

```sh
python3 -m pip install -e .
```

From the repository root:

```sh
chmod +x agent_profile.py
mkdir -p "$HOME/.local/bin"
ln -sf "$PWD/agent_profile.py" "$HOME/.local/bin/agent-profile"
```

Make sure `~/.local/bin` is on your `PATH`.

## Create a Profile

```sh
agent-profile init demo --tool claude --purpose "Skills, MCP, and plugin testing"
```

This creates:

```text
~/agent-profiles/demo/
  config/
    config.toml  # Codex; Claude Code profiles contain settings.json
  workspace/
  meta.json
```

It also updates:

```text
~/agent-profiles/registry.json
```

## List Profiles

```sh
agent-profile list
```

## Show a Profile Path

```sh
agent-profile path demo
```

## Run Codex or Claude Code in a Profile

```sh
agent-profile run demo
```

To pass a custom command:

```sh
agent-profile run demo env
```

The command runs from the profile workspace with the selected agent's config variable pointed at the profile config directory. This is the core behavior of the tool.

By default, the command inherits the current shell environment. To use a minimal environment instead:

```sh
agent-profile run demo --clean-env
```

Clean mode keeps basic process variables such as `PATH`, `HOME`, `TMPDIR`, locale, and terminal settings. Other variables—including API keys and cloud credentials—are excluded unless explicitly passed:

```sh
agent-profile run demo --clean-env --env OPENAI_API_KEY="$OPENAI_API_KEY"
```

`CODEX_HOME`, `CLAUDE_CONFIG_DIR`, `HOME`, and `PWD` are reserved and always point to the selected profile context.

## Clone a Profile

```sh
agent-profile clone SOURCE DEST
```

This copies configuration such as skills and rules into a new profile and creates an empty workspace. Authentication, history, sessions, caches, logs, SQLite databases, and other runtime state are excluded.

## Compare Configuration

```sh
agent-profile diff NAME
```

This compares the profile configuration with the corresponding main agent configuration (`~/.codex/config.toml` or `~/.claude/settings.json`). Sensitive-looking values are redacted. Exit status is `1` when differences are found.

## Reset a Profile

```sh
agent-profile reset NAME --yes
```

Reset deletes and recreates the selected profile while retaining its registered purpose and notes. The `--yes` confirmation is required.

## Export a Profile

```sh
agent-profile export NAME --output NAME-export.tar.gz
```

Exports metadata and configuration into a private archive. Authentication, history, sessions, caches, logs, SQLite databases, generated images, and workspace contents are excluded. Existing output files are never overwritten.

## Check Your Setup

```sh
agent-profile doctor
```

`doctor` prints the profile root, checks whether `codex` and `claude` are on your `PATH`, and reminds you that TCP ports are shared.

## Reuse Existing Profiles

```sh
agent-profile init demo --reuse --purpose "Updated purpose"
```

`--reuse` preserves the existing `config/` and `workspace/` directories while updating metadata. It is not a reset command.

## Port Collisions

Each profile gets its own config and workspace, but it is not a VM, container, network namespace, or security boundary. Environment variables, host filesystem permissions, running services, and TCP ports are still shared by your operating system.

If your shell has secrets such as `OPENAI_API_KEY`, GitHub tokens, cloud credentials, or database URLs, commands launched through `agent-profile run` inherit them by default.

If a skill, MCP server, plugin, dev server, database, or helper service binds to a port such as `3000`, `5173`, `8000`, or `11434`, it can collide with the same service from your main Codex or Claude Code config or another profile.

Use explicit unique ports when running multiple environments at the same time.
