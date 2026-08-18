# Contributing

Thanks for helping improve Agent Profile.

## Development

Run the test suite before opening a pull request:

```sh
python3 -m unittest discover -s tests
```

## Guidelines

- Keep the CLI dependency-free unless a dependency removes significant complexity.
- Do not commit profile runtime state such as `auth.json`, `history.jsonl`, sessions, caches, or SQLite files.
- Document behavior that affects user safety or local machine state.
- Keep examples aligned with the public command name: `agent-profile`.
