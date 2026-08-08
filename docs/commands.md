# Commands

`codex-sandbox` is a small Python CLI for creating isolated Codex workspaces.

## Install Locally

From the repository root:

```sh
chmod +x codex_sandbox.py
ln -sf "$PWD/codex_sandbox.py" "$HOME/.local/bin/codex-sandbox"
```

Make sure `~/.local/bin` is on your `PATH`.

## Create a Sandbox

```sh
codex-sandbox init agent-lab --purpose "Skills, MCP, and plugin testing"
```

This creates:

```text
~/cc-sandboxes/agent-lab/
  config/
  workspace/
  meta.json
```

It also updates:

```text
~/cc-sandboxes/registry.json
```

## List Sandboxes

```sh
codex-sandbox list
```

## Show a Sandbox Path

```sh
codex-sandbox path agent-lab
```

## Run Codex in a Sandbox

```sh
codex-sandbox run agent-lab
```

To pass a custom command:

```sh
codex-sandbox run agent-lab codex --sandbox workspace-write
```

The command runs from the sandbox workspace with `CODEX_HOME` pointed at the sandbox config directory.

## Port Collisions

Each sandbox gets its own config and workspace, but TCP ports are still shared by your operating system. If a skill, MCP server, plugin, dev server, database, or helper service binds to a port such as `3000`, `5173`, `8000`, or `11434`, it can collide with the same service from your main Codex config or another sandbox.

Use explicit unique ports when running multiple environments at the same time.
