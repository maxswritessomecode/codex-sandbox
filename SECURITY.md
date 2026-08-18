# Security

Agent Profile is designed to keep Codex or Claude Code configuration and workspace files separate from your main `~/.codex` setup. It is not a VM, container, network namespace, process profile, or security boundary.

## What Is Isolated

- `CODEX_HOME` points at the selected profile's `config/` directory.
- Commands run from the selected profile's `workspace/` directory.
- Profile metadata is stored under the configured profile root.

## What Is Not Isolated

- TCP ports are shared with your host and all other profiles.
- Environment variables are inherited by launched commands.
- Running processes are normal host processes.
- System keychains, browsers, OS services, and other host-level resources are not isolated by this tool.
- Tools, skills, MCP servers, plugins, and helper services can still access whatever their own permissions allow.

## Port Collisions

If anything you install or run binds a TCP port, it can collide with services from your main Codex or Claude Code config or another profile. Common examples include dev servers, local databases, Ollama, MCP servers, and plugin helper processes.

Use explicit, unique ports when running multiple environments side by side.

## Environment Variables

Commands launched with `agent-profile run` inherit your current shell environment by default. If your shell exports secrets such as `OPENAI_API_KEY`, GitHub tokens, cloud credentials, or database URLs, those values are available to the launched command.

Use `agent-profile run NAME --clean-env` to start with a minimal environment. Explicitly pass required variables with `--env NAME=VALUE`. The launcher always controls `CODEX_HOME`, `HOME`, and `PWD` so a command cannot redirect itself to the main Codex or Claude Code home through those options.

## Reporting Issues

Open a GitHub issue for security-relevant behavior that is safe to discuss publicly. Do not post secrets, tokens, session logs, `auth.json`, or private Codex or Claude Code config in an issue.
