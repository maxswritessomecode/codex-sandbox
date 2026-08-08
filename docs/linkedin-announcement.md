# LinkedIn Announcement Draft

I just released Codex Sandbox: a small CLI for creating disposable Codex workspaces.

It gives you a clean place to test skills, MCP servers, plugins, memories, feature flags, and other Codex config experiments without polluting your main `~/.codex` setup.

Why I built it:

- I wanted quick, named Codex workspaces for experiments.
- I wanted a cleaner way to separate plugin/skill testing from my daily config.
- I wanted a safer default for public examples: no auth files, sessions, caches, or SQLite runtime state in git.

Quick start:

```sh
git clone https://github.com/maxswritessomecode/codex-sandbox.git
cd codex-sandbox
python3 -m pip install -e .
codex-sandbox init demo --purpose "Skills, MCP, and plugin testing"
codex-sandbox run demo
```

One important caveat: it isolates Codex config and workspace files, not your whole machine. It is not a VM or container. Environment variables and TCP ports are still shared, so use explicit ports for local servers and avoid exporting secrets you do not want available to launched commands.

Repo: https://github.com/maxswritessomecode/codex-sandbox
