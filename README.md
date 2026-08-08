# Codex Sandbox

Disposable workspaces for Codex agents, MCP tools, and plugin testing.

Codex Sandbox gives you a clean place to test agent configs without polluting your main `~/.codex` setup. Use it when you want to try MCP servers, plugins, memories, or feature flags in an isolated workspace that is easy to reset.

## Install

```sh
git clone https://github.com/maxswritessomecode/codex-sandbox.git
cd codex-sandbox
chmod +x codex_sandbox.py
ln -sf "$PWD/codex_sandbox.py" "$HOME/.local/bin/codex-sandbox"
```

Make sure `~/.local/bin` is on your `PATH`.

## Quick Start

```sh
codex-sandbox init mcp-testing --purpose "MCP server testing"
codex-sandbox run mcp-testing
```

`codex-sandbox run` launches Codex from the sandbox workspace with `CODEX_HOME` pointed at that sandbox's config directory.

## Why Use It

- Keep experimental Codex config separate from your daily setup.
- Test MCP servers and plugins in a named workspace.
- Capture project purpose and metadata in one place.
- Avoid accidentally publishing local auth, session, cache, and SQLite state.

## Commands

```sh
codex-sandbox init NAME --purpose "What this sandbox is for"
codex-sandbox list
codex-sandbox path NAME
codex-sandbox run NAME
codex-sandbox run NAME codex --sandbox workspace-write
```

See [docs/commands.md](docs/commands.md) for details.

## Suggested Layout

```text
codex-sandbox/
  README.md
  ai_agent.md
  codex_sandbox.py
  docs/
  tests/
```

Local runtime state should stay out of git:

```text
config/
sandboxes/
sessions/
cache/
*.sqlite*
auth.json
history.jsonl
```

## Example Sandbox Metadata

```json
{
  "name": "codex-sandbox",
  "purpose": "Disposable Codex workspace for MCP and plugin testing",
  "tool": "codex"
}
```

## Development

Run the tests with:

```sh
python3 -m unittest discover -s tests
```

## Positioning

Codex Sandbox is for developers and technical operators who want a safe place to test agent workflows before moving them into their main Codex environment.
