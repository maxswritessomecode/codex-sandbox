# LinkedIn Announcement Draft

I just released Codex Sandbox: a tiny CLI for named Codex config/workspace environments.

This is not a universal developer tool, and it is not a security sandbox. It is for Codex power users who keep testing skills, MCP servers, plugins, memories, feature flags, or alternate config states and do not want to clutter their daily `~/.codex` setup.

Why I built it:

- I wanted quick, named Codex workspaces for experiments.
- I wanted a cleaner way to separate plugin/skill testing from my daily config.
- I wanted a safer default for public examples: no auth files, sessions, caches, or SQLite runtime state in git.

Under the hood, it is deliberately simple: launch Codex with a sandbox-specific `CODEX_HOME` and working directory.

Quick start:

```sh
git clone https://github.com/maxswritessomecode/codex-sandbox.git
cd codex-sandbox
python3 -m pip install -e .
codex-sandbox init demo --purpose "Skills, MCP, and plugin testing"
codex-sandbox run demo
```

One important caveat: it isolates Codex config and workspace files, not your whole machine. It is not a VM or container. Environment variables and TCP ports are still shared, so use explicit ports for local servers and avoid exporting secrets you do not want available to launched commands.

My honest framing: useful for people who frequently switch between Codex setups; probably unnecessary if you only use one stable config.

Repo: https://github.com/maxswritessomecode/codex-sandbox
