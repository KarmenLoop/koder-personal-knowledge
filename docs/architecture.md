# Architecture

The project has two parts: a portable skill that guides the host agent, and a local Python storage tool. Identity, model access, channel transport, and computer execution remain host responsibilities.

## Data layout

SQLite is the source of truth. The database contains:

- `meta`: schema version, owner identity, and creation time.
- `spaces`: stable names for personal or project knowledge spaces.
- `grants`: per-space reader/writer access for verified principals.
- `entries`: facts, inferences, references, sources, statuses, tags, and attachment metadata.
- `tombstones`: deleted record IDs, deletion times, and optional event hashes.

Each original file is copied to `library/<sha256>.bin`. Identical contents share a stored copy. The entry retains the original filename, size, hash, and extraction state. The tool leaves the input file untouched.

HTML, Markdown, and JSON under `views/` are generated snapshots. They are useful for inspection and portability; editing a snapshot does not change the authoritative record. Make knowledge changes through the tool, then regenerate views.

## Record lifecycle

```text
Explicit statement -> fact -> active
Selected material  -> reference -> active
Behavioral pattern -> inference -> unconfirmed

Owner correction or confirmation:
  current record -> superseded
  new source-backed record -> active

Owner deletion:
  record removed -> minimal tombstone
  unused attachment removed -> views regenerated
```

History remains inspectable until the owner deletes it. Default retrieval excludes unconfirmed and superseded records. Forgetting an entire topic requires removing its older versions as well as the latest entry.

## Writes and recovery

Writes use `BEGIN IMMEDIATE`, an eight-second busy timeout, and parameterized SQL. Concurrent writers serialize through SQLite rather than sharing mutable in-memory history. Event keys deduplicate retries; a changed payload under the same key is a conflict.

Generated files and originals use temporary files followed by atomic replacement. These filesystem writes and the SQLite commit do not form one cross-filesystem transaction. After an interruption, derived views may be out of date or inconsistent with the committed database. Rebuild them with `render` after recovery. Backups and restores should include both the database and managed original files.

No stale-lock takeover, scheduled maintenance daemon, migration service, or second database is introduced. An existing library with an unknown schema is rejected rather than rewritten.

## Retrieval

Search scores matching terms in titles, bodies, and tags, with extra weight for titles. Chinese text fragments help match questions to shorter stored phrases. It currently scans eligible records in the requested space; it is intended as a small, inspectable baseline, not a large-scale search server.

Results include the record ID, current status, source, and a bounded excerpt. The serialized search result respects its character budget. Full-text reads are paginated separately, and list output is for inspection. The host is responsible for the final model token budget.

There are no embeddings, network model requests, OCR dependencies, or vector database services in the tool.

## Access model

The owner can access every space and manage grants. A reader can retrieve from a granted space. A writer can also add records and imports. Only the owner can supersede existing records, delete them, change grants, or render all spaces.

Principals are trusted host inputs. Application checks do not authenticate a network caller or stop a process that can read the database file. Shared deployments need a host wrapper that fixes the root and derives principal/space from the verified request context.

Source content is untrusted data. It cannot change these access rules or grant execution authority. Refer to the [host contract](../koder-personal-knowledge/references/host-integration.md) and [privacy guide](privacy.md) before exposing the tool to a messaging gateway.

## Extension points

Useful extensions include source-bound document extraction, improved local ranking, a paged viewer, and host-specific knowledge tools. Cross-device synchronization needs an explicit identity, conflict, deletion, and ownership protocol; copying a live SQLite file into a sync folder is not that protocol.
