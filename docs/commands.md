# Commands

`codex-sandbox` is a small Python CLI for creating isolated Codex workspaces.

## Install Locally

Prerequisite: install and authenticate the Codex CLI first. Each sandbox uses a separate `CODEX_HOME`, so the first run for a sandbox may ask you to sign in or initialize Codex config.

Recommended:

```sh
pipx install git+https://github.com/maxswritessomecode/codex-sandbox.git
```

If you do not have `pipx`, install it first or use the local development/manual install path below.

For local development:

```sh
python3 -m pip install -e .
```

From the repository root:

```sh
chmod +x codex_sandbox.py
mkdir -p "$HOME/.local/bin"
ln -sf "$PWD/codex_sandbox.py" "$HOME/.local/bin/codex-sandbox"
```

Make sure `~/.local/bin` is on your `PATH`.

## Create a Sandbox

```sh
codex-sandbox init demo --purpose "Skills, MCP, and plugin testing"
```

This creates:

```text
~/codex-sandboxes/demo/
  config/
    config.toml
  workspace/
  meta.json
```

It also updates:

```text
~/codex-sandboxes/registry.json
```

## List Sandboxes

```sh
codex-sandbox list
```

## Show a Sandbox Path

```sh
codex-sandbox path demo
```

## Run Codex in a Sandbox

```sh
codex-sandbox run demo
```

To pass a custom command:

```sh
codex-sandbox run demo env
```

The command runs from the sandbox workspace with `CODEX_HOME` pointed at the sandbox config directory.

## Check Your Setup

```sh
codex-sandbox doctor
```

`doctor` prints the sandbox root, checks whether `codex` is on your `PATH`, and reminds you that TCP ports are shared.

## Reuse Existing Sandboxes

```sh
codex-sandbox init demo --reuse --purpose "Updated purpose"
```

`--reuse` preserves the existing `config/` and `workspace/` directories while updating metadata. It is not a reset command.

## Port Collisions

Each sandbox gets its own config and workspace, but it is not a VM, container, network namespace, or security boundary. Environment variables, host filesystem permissions, running services, and TCP ports are still shared by your operating system.

If your shell has secrets such as `OPENAI_API_KEY`, GitHub tokens, cloud credentials, or database URLs, commands launched through `codex-sandbox run` inherit them by default.

If a skill, MCP server, plugin, dev server, database, or helper service binds to a port such as `3000`, `5173`, `8000`, or `11434`, it can collide with the same service from your main Codex config or another sandbox.

Use explicit unique ports when running multiple environments at the same time.
