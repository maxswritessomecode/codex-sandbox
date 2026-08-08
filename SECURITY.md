# Security

Codex Sandbox is designed to keep Codex configuration and workspace files separate from your main `~/.codex` setup. It is not a VM, container, network namespace, process sandbox, or security boundary.

## What Is Isolated

- `CODEX_HOME` points at the selected sandbox's `config/` directory.
- Commands run from the selected sandbox's `workspace/` directory.
- Sandbox metadata is stored under the configured sandbox root.

## What Is Not Isolated

- TCP ports are shared with your host and all other sandboxes.
- Environment variables are inherited by launched commands.
- Running processes are normal host processes.
- System keychains, browsers, OS services, and other host-level resources are not isolated by this tool.
- Tools, skills, MCP servers, plugins, and helper services can still access whatever their own permissions allow.

## Port Collisions

If anything you install or run binds a TCP port, it can collide with services from your main Codex config or another sandbox. Common examples include dev servers, local databases, Ollama, MCP servers, and plugin helper processes.

Use explicit, unique ports when running multiple environments side by side.

## Environment Variables

Commands launched with `codex-sandbox run` inherit your current shell environment. If your shell exports secrets such as `OPENAI_API_KEY`, GitHub tokens, cloud credentials, or database URLs, those values are available to the launched command.

## Reporting Issues

Open a GitHub issue for security-relevant behavior that is safe to discuss publicly. Do not post secrets, tokens, session logs, `auth.json`, or private Codex config in an issue.
