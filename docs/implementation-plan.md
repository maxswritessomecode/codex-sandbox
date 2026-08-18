# Implementation Plan and Completion Summary

## Scope

Agent Profile provides named Codex or Claude Code configuration and workspace profiles. It isolates `CODEX_HOME` and the working directory, but it is not a VM, container, network namespace, or operating-system security boundary.

## Completed in 0.2.0

### Core hardening

- Canonical absolute profile paths.
- Safe TOML workspace-path serialization.
- Rejection of symlinked profile, config, and workspace directories.
- Owner-only permissions for newly created profile state.
- Registry schema validation.
- Locked, durable, atomic registry writes.

### Environment and diagnostics

- Compatible inherited-environment mode remains the default.
- Added opt-in `--clean-env` mode.
- Added explicit repeatable `--env NAME=VALUE` passthrough.
- Reserved `CODEX_HOME`, `HOME`, and `PWD` variables cannot be overridden.
- Expanded `doctor` checks for Codex or Claude Code availability, root health, permissions, registry validity, incomplete profiles, and references to the main Codex or Claude Code home.

### Lifecycle commands

```sh
agent-profile clone SOURCE DEST
agent-profile diff NAME
agent-profile reset NAME --yes
agent-profile export NAME
```

- `clone` copies configuration while excluding authentication and runtime state, rewrites the project path, and creates an empty workspace.
- `diff` compares profile and main configuration with sensitive-looking values redacted.
- `reset` requires explicit `--yes` confirmation and preserves registered purpose and notes.
- `export` creates a private configuration archive that excludes workspace contents, authentication, sessions, caches, logs, and databases.

## Verification

- 22 unit tests pass.
- Temporary-root smoke tests pass for clone, export, reset, and clean environment execution.
- `git diff --check` passes.
- Version is `0.2.0`.

## Future work

- Import support for exported archives.
- Optional templates such as `blank`, `skills`, `mcp`, and `plugin-dev`.
- Additional platform-specific locking support if Windows becomes a target.
