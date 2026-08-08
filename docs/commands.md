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
codex-sandbox init mcp-testing --purpose "MCP server testing"
```

This creates:

```text
~/cc-sandboxes/mcp-testing/
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
codex-sandbox path mcp-testing
```

## Run Codex in a Sandbox

```sh
codex-sandbox run mcp-testing
```

To pass a custom command:

```sh
codex-sandbox run mcp-testing codex --sandbox workspace-write
```

The command runs from the sandbox workspace with `CODEX_HOME` pointed at the sandbox config directory.
