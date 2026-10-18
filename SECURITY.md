# Security Reporting

Do not post secrets, personal knowledge files, private messages, or an actionable exploit in a public issue.

Use GitHub's **Report a vulnerability** feature in this repository's Security tab when private reporting is available. If it is unavailable, open a minimal issue asking the maintainers for a private contact route. Leave the technical details out until a private route is established.

Useful report details include the affected version/commit, required host configuration, expected access boundary, and a minimal reproduction using synthetic data. Include observed behavior and impact. Do not send a copy of a real personal library.

## Scope and deployment assumptions

The script runs as the local OS account and accepts a principal from its host. It is not a network authentication service or a sandbox. The host must protect its root path, derive identities from verified bindings, and restrict the tools exposed to shared-channel conversations.

Secret-pattern filtering is a supplemental check, not a credential vault or complete data-loss prevention system. Encryption at rest, message delivery, account binding, provider access, and OS permissions belong to the host/deployment.

Security fixes target the latest released version. Older releases may need an upgrade rather than a separate backport. Response timing depends on maintainer availability; this project does not offer a guaranteed security SLA.
