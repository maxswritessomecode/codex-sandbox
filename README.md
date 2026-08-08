# Codex Sandbox

Disposable workspaces for Codex agents, skills, MCP tools, plugins, and config experiments.

Codex Sandbox gives you a clean place to test agent configs without polluting your main `~/.codex` setup. Use it when you want to try skills, MCP servers, plugins, memories, feature flags, or workflow experiments in an isolated workspace that is easy to discard and recreate.

## Install

Prerequisite: install and authenticate the Codex CLI first. Because each sandbox gets its own `CODEX_HOME`, the first `codex-sandbox run NAME` may ask you to sign in or initialize Codex config for that sandbox.

Recommended:

```sh
pipx install git+https://github.com/maxswritessomecode/codex-sandbox.git
```

If you do not have `pipx`, install it first or use the local development/manual install path below.

For local development:

```sh
git clone https://github.com/maxswritessomecode/codex-sandbox.git
cd codex-sandbox
python3 -m pip install -e .
```

Manual no-packaging install:

```sh
git clone https://github.com/maxswritessomecode/codex-sandbox.git
cd codex-sandbox
chmod +x codex_sandbox.py
mkdir -p "$HOME/.local/bin"
ln -sf "$PWD/codex_sandbox.py" "$HOME/.local/bin/codex-sandbox"
```

Make sure `~/.local/bin` is on your `PATH`.

## Quick Start

```sh
codex-sandbox init demo --purpose "Skills, MCP, and plugin testing"
codex-sandbox run demo
```

`codex-sandbox run` launches Codex from the sandbox workspace with `CODEX_HOME` pointed at that sandbox's config directory.

That creates:

```text
~/codex-sandboxes/demo/
  config/
    config.toml
  workspace/
  meta.json
```

## Why Use It

- Keep experimental Codex config separate from your daily setup.
- Test skills, MCP servers, plugins, and feature flags in a named workspace.
- Capture project purpose and metadata in one place.
- Avoid accidentally publishing local auth, session, cache, and SQLite state.

## Important Note

Codex Sandbox is config isolation, not a security boundary. It does not containerize processes, virtualize the network, scrub environment variables, or prevent tools from accessing files and services your normal user account can access.

Anything you install or run that binds a TCP port can still collide with services from your main Codex setup or another sandbox if they use the same host and port. Give local servers explicit, unique ports when you run multiple environments side by side.

If your shell has secrets such as `OPENAI_API_KEY`, GitHub tokens, cloud credentials, or database URLs, commands launched through `codex-sandbox run` inherit them by default.

## Commands

```sh
codex-sandbox init NAME --purpose "What this sandbox is for"
codex-sandbox list
codex-sandbox path NAME
codex-sandbox run NAME
codex-sandbox doctor
codex-sandbox run NAME env
```

See [docs/commands.md](docs/commands.md) for details.

## Repository Layout

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
  "purpose": "Disposable Codex workspace for skills, MCP, and plugin testing",
  "tool": "codex"
}
```

## Development

Run the tests with:

```sh
python3 -m unittest discover -s tests
```

## License

MIT

## Positioning

Codex Sandbox is for developers and technical operators who want a safe place to test agent workflows before moving them into their main Codex environment.
