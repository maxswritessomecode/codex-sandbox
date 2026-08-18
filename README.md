# Codex Sandbox (archived)

This project has moved to [Agent Profile](https://github.com/maxswritessomecode/agent-profile).

Agent Profile is the renamed, multi-agent version of this tool. It supports named configuration profiles and workspaces for both Codex and Claude Code.

Please use the new repository for current code, releases, documentation, and issues.

---

# Agent Profile

A small CLI for named Codex and Claude Code configuration profiles and workspaces.

Agent Profile is for Codex and Claude Code users who experiment with skills, MCP servers, plugins, memories, feature flags, or alternate config states without cluttering their daily setup.

It is intentionally small. Under the hood, it launches the selected agent with a profile-specific config directory and working directory:

```sh
CODEX_HOME=~/agent-profiles/demo/config
# Claude Code profiles use CLAUDE_CONFIG_DIR instead.
cwd=~/agent-profiles/demo/workspace
codex
```

Use it when that convention is worth naming, listing, and repeating.

## Install

Prerequisite: install and authenticate the Codex or Claude Code CLI first. Each profile gets its own agent configuration directory.

Recommended:

```sh
pipx install git+https://github.com/maxswritessomecode/agent-profile.git
```

If you do not have `pipx`, install it first or use the local development/manual install path below.

For local development:

```sh
git clone https://github.com/maxswritessomecode/agent-profile.git
cd agent-profile
python3 -m pip install -e .
```

Manual no-packaging install:

```sh
git clone https://github.com/maxswritessomecode/agent-profile.git
cd agent-profile
chmod +x agent_profile.py
mkdir -p "$HOME/.local/bin"
ln -sf "$PWD/agent_profile.py" "$HOME/.local/bin/agent-profile"
```

Make sure `~/.local/bin` is on your `PATH`.

## Quick Start

```sh
agent-profile init demo --tool claude --purpose "Skills, MCP, and plugin testing"
agent-profile run demo
```

`agent-profile run` launches the configured agent from the profile workspace. Codex receives `CODEX_HOME`; Claude Code receives `CLAUDE_CONFIG_DIR`.

That creates:

```text
~/agent-profiles/demo/
  config/                 # config.toml for Codex; settings.json for Claude Code
  workspace/
  meta.json
```

## Why Use It

- Keep experimental Codex or Claude Code config separate from your daily setup.
- Test skills, MCP servers, plugins, and feature flags in a named workspace.
- Capture project purpose and metadata in one place.
- Avoid accidentally publishing local auth, session, cache, and SQLite state.

## Who It Is For

- Codex or Claude Code users who maintain more than one config state.
- People testing skills, MCP servers, or plugins before adding them to their main setup.
- Tutorial authors who want repeatable clean Codex or Claude Code examples.
- Developers who want separate personal, work, demo, and experiment Codex or Claude Code homes.

## Who It Is Not For

- Casual Codex or Claude Code users with one stable config.
- People expecting Docker-style isolation.
- People who only need a one-off command like `CODEX_HOME=/tmp/codex-test codex`.
- Anyone looking for a security boundary. Use containers or VMs for that.

## Important Note

Agent Profile is config isolation, not a security boundary. It does not containerize processes, virtualize the network, scrub environment variables, or prevent tools from accessing files and services your normal user account can access.

Anything you install or run that binds a TCP port can still collide with services from your main Codex or Claude Code setup or another profile if they use the same host and port. Give local servers explicit, unique ports when you run multiple environments side by side.

If your shell has secrets such as `OPENAI_API_KEY`, GitHub tokens, cloud credentials, or database URLs, commands launched through `agent-profile run` inherit them by default.

For a minimal environment, use:

```sh
agent-profile run demo --clean-env
```

This preserves basic runtime variables and adds the selected agent's config variable, but excludes unrelated shell variables and secrets. Add a variable explicitly when needed:

```sh
agent-profile run demo --clean-env --env OPENAI_API_KEY="$OPENAI_API_KEY"
```

`CODEX_HOME`, `CLAUDE_CONFIG_DIR`, `HOME`, and `PWD` are controlled by the launcher and cannot be overridden.

## Commands

```sh
agent-profile init NAME --purpose "What this profile is for"
agent-profile list
agent-profile path NAME
agent-profile run NAME
agent-profile doctor
agent-profile run NAME env
agent-profile run NAME --clean-env
agent-profile clone SOURCE DEST
agent-profile diff NAME
agent-profile reset NAME --yes
agent-profile export NAME
```

See [docs/commands.md](docs/commands.md) for details.

## Repository Layout

```text
agent-profile/
  README.md
  ai_agent.md
  agent_profile.py
  docs/
  tests/
```

Local runtime state should stay out of git:

```text
config/
profiles/
sessions/
cache/
*.sqlite*
auth.json
history.jsonl
```

## Example Profile Metadata

```json
{
  "name": "agent-profile",
  "purpose": "Disposable Codex or Claude Code workspace for skills, MCP, and plugin testing",
  "tool": "codex"
}
```

## Roadmap

Lifecycle commands are available for copying configuration, comparing profiles, resetting a profile, and exporting a safe configuration archive. Templates and import support remain future work.

## Development

Run the tests with:

```sh
python3 -m unittest discover -s tests
```

## License

MIT

## Positioning

Agent Profile is a convenience tool for repeatable Codex or Claude Code config/workspace experiments. It is useful when you frequently switch between Codex or Claude Code setups; it is probably unnecessary if you only use one setup.
