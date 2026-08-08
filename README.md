# Codex Sandbox

Disposable workspaces for Codex agents, MCP tools, and plugin testing.

Codex Sandbox gives you a clean place to test agent configs without polluting your main `~/.codex` setup. Use it when you want to try MCP servers, plugins, memories, or feature flags in an isolated workspace that is easy to reset.

## Why Use It

- Keep experimental Codex config separate from your daily setup.
- Test MCP servers and plugins in a named workspace.
- Capture project purpose and metadata in one place.
- Avoid accidentally publishing local auth, session, cache, and SQLite state.

## Suggested Layout

```text
codex-sandbox/
  README.md
  ai_agent.md
  docs/
  examples/
  templates/
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

## Positioning

Codex Sandbox is for developers and technical operators who want a safe place to test agent workflows before moving them into their main Codex environment.
