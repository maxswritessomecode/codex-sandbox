# Changelog

## 0.2.0 - 2026-08-18

- Added clean-environment execution with explicit variable passthrough.
- Added stronger diagnostics and permission checks to `doctor`.
- Added `clone`, `diff`, `reset`, and safe `export` lifecycle commands.
- Hardened paths, registry validation/locking, TOML serialization, and private state creation.

## 0.1.0 - 2026-08-08

- Initial public release.
- Added `agent-profile init`, `list`, `path`, `run`, and `doctor`.
- Added packaging metadata for `pipx` and editable installs.
- Set the default profile root to `~/agent-profiles`.
- Added documentation for isolated Codex config/workspaces and TCP port collision limits.
- Repositioned the project as config/workspace separation for Codex power users, not broad security sandboxing.
