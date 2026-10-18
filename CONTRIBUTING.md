# Contributing

Thanks for helping make personal agent memory useful and understandable. Focused bug fixes, clearer documentation, and host integration examples are welcome.

## Before you start

For a larger change, open an issue describing the user problem, the proposed behavior, and the parts you expect to touch. Keep the local store, host identity, channel delivery, and execution permissions separate.

This project uses Python 3.9+ and the standard library. Avoid adding runtime dependencies unless the benefit is clear and the maintenance cost is discussed first.

## Local development

```sh
python3 -B -m unittest discover -s tests -v
```

Tests create synthetic libraries in temporary directories. Keep them that way. Never make a test depend on a contributor's personal knowledge, logged-in messaging account, paid API, or local credentials.

For a storage or retrieval change, add a regression that fails for the actual bug, then make the change and run the full suite. Preserve existing assertions. Include a negative case when working on access, deletion, event deduplication, or path handling.

The suite includes Unicode fixtures for multilingual retrieval. They are intentionally written as escapes in the source. A symlink test may skip on Windows only when the account lacks the specific privilege to create symlinks; report that skip honestly.

## Pull requests

Describe the concrete problem and the resulting behavior. Include the exact validation command, exit code, and relevant results. State platform or integration limits instead of treating a configured CI job as a completed run.

Keep changes scoped. Do not upload personal databases, managed originals, generated owner-wide views, tokens, or raw support logs. The repository's ignore rules are a starting point, not a replacement for reviewing your diff.

For documentation, use clear US English. Describe available behavior, provide runnable examples, and distinguish the storage tool's responsibilities from the host's. Update the relevant reference rather than duplicating a long command manual across several files.

## License and conduct

Contributions are made under this repository's MIT License. No separate contributor license agreement is required for this project. Follow the [code of conduct](CODE_OF_CONDUCT.md), and use the [security reporting process](SECURITY.md) for sensitive issues.
