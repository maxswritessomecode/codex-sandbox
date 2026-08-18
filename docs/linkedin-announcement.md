# LinkedIn Announcement Draft

I just released Agent Profile: a tiny CLI for named Codex or Claude Code config/workspace environments.

This is not a universal developer tool, and it is not a security profile. It is for Codex or Claude Code power users who keep testing skills, MCP servers, plugins, memories, feature flags, or alternate config states and do not want to clutter their daily `~/.codex` setup.

Why I built it:

- I wanted quick, named Codex or Claude Code workspaces for experiments.
- I wanted a cleaner way to separate plugin/skill testing from my daily config.
- I wanted a safer default for public examples: no auth files, sessions, caches, or SQLite runtime state in git.

Under the hood, it is deliberately simple: launch Codex or Claude Code with a profile-specific `CODEX_HOME` and working directory.

Quick start:

```sh
git clone https://github.com/maxswritessomecode/agent-profile.git
cd agent-profile
python3 -m pip install -e .
agent-profile init demo --purpose "Skills, MCP, and plugin testing"
agent-profile run demo
```

One important caveat: it isolates Codex or Claude Code config and workspace files, not your whole machine. It is not a VM or container. Environment variables and TCP ports are still shared, so use explicit ports for local servers and avoid exporting secrets you do not want available to launched commands.

My honest framing: useful for people who frequently switch between Codex or Claude Code setups; probably unnecessary if you only use one stable config.

Repo: https://github.com/maxswritessomecode/agent-profile
