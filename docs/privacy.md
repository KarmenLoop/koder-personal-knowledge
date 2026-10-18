# Privacy and Data Handling

## What stays local

The bundled storage tool makes no network requests. It writes the database, selected file copies, and readable views to the configured directory. It has no telemetry client, cloud account, web server, or background file collector.

Your host agent is a separate system. It may send your message, retrieved excerpts, or selected files to a model provider or connected app. Choose that provider and the host's logging/retention settings accordingly. Local storage alone does not make a hosted-model conversation offline.

## What is collected

The skill guides an agent to save explicit, useful facts from conversations and archive files you provide or select. It does not instruct the agent to scan the whole computer or read private app databases.

A record may include a preference, relationship, work detail, source reference, speaker, timestamp, tags, and an optional file copy. Behavioral hypotheses are labeled as unconfirmed inferences. An agent should distinguish the user's statements from quoted messages, role-play, or another group member's comments.

The knowledge base must not become a credential store. The tool rejects common secret patterns and credential file extensions, but that filter is incomplete, especially for binary files. The host should keep passwords, tokens, API keys, and authentication headers out before calling it.

## Who can read it

The full HTML page, JSON catalog, and Markdown directory contain every space. They are owner views, not public exports. Do not publish them, commit them to Git, or attach the complete page to a shared chat.

An owner can share a space with a verified group principal. This can let all members of the associated group use facts originally recorded in the owner's private conversation. Review that scope before granting it. Other members' private spaces are not automatically merged.

Reader/writer grants are enforced by the script for trusted host calls. They do not stop a local process that already has filesystem access. POSIX library initialization uses restrictive directory permissions; Windows inherits directory ACLs. The host deployment must secure the local account and directory.

There is no built-in encryption-at-rest layer. Use appropriate OS account protection and disk encryption where needed. The tool does not provision or change those settings.

## Correcting and forgetting

Corrections create a new record and mark the old one superseded. The old content stays in inspection history until it is deleted. Ordinary search excludes it.

`forget` removes the chosen record, generated views of it, and a managed original copy if no other record uses that copy. A minimal tombstone retains the deleted ID, time, and an event hash to prevent the same message retry from restoring the record.

To forget a subject completely, inspect and delete every relevant version and duplicate reference. The script does not delete original files, messages from connected apps, host logs, model-provider records, backups, or OS snapshots. It cannot promise physical erasure from an SSD or other storage medium.

## Files and model exposure

An archived binary marked `attachment_only` has not been text-indexed. External extraction may expose content to whichever tool the host chooses. Prefer local parsers when local processing is required, and confirm that any external parser is acceptable before using it.

Retrieval returns focused text rather than the entire library. This reduces prompt size and unnecessary exposure, but it is still a disclosure to the model and the recipient of the response. The host should preserve the verified reply route and recheck access before delivery.

## Backups and sharing

Keep backups separate from public source repositories. Back up when no writes are active, or use a SQLite-aware method that also preserves the referenced files. Treat the HTML, Markdown, and catalog copies as sensitive too.

For a shared-channel deployment, use the restricted host tools described in the [integration guide](../koder-personal-knowledge/references/host-integration.md). An unrestricted shell with access to the library defeats the application-level access checks.
