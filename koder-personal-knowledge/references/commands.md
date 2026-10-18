# Command Reference

Run commands from the repository root using `python3 koder-personal-knowledge/scripts/knowledge.py`. On Windows, use `python`. If the skill is already installed, locate its directory and use `python3 scripts/knowledge.py` there.

Global options come **before** the subcommand:

```text
knowledge.py [--root PATH] [--principal VERIFIED_ID] [--space SPACE] COMMAND ...
```

The examples below use a synthetic `local-owner` principal. In a live deployment, the host supplies the verified principal and fixed root. Omitted `--root` values assume that the host has set `KODER_KNOWLEDGE_ROOT` to the correct library.

## Initialize and locate a library

```sh
python3 koder-personal-knowledge/scripts/knowledge.py path
python3 koder-personal-knowledge/scripts/knowledge.py init --owner local-owner
```

`path` prints the default root without creating files. `init` creates an empty library or reopens one with the same owner. It rejects an unrelated nonempty directory and refuses to replace an existing owner.

Windows prefers `D:\KoderKnowledge`. Without D:, it uses the user's C: profile; a redirected profile falls back to `C:\Users\<username>\KoderKnowledge`. macOS and Linux use `~/KoderKnowledge`. An unwritable location is an error, not a reason to create a second library silently.

Persist the returned absolute root in host configuration. `--root` overrides the environment setting; changing either value does not migrate data.

```text
KoderKnowledge/
  knowledge.sqlite3        Authoritative records, spaces, grants, and tombstones
  library.json             Storage format and location information
  library/<SHA256>.bin      Original file copies, deduplicated by content
  views/index.html         Complete offline view for the local owner
  views/catalog.json       Complete structured snapshot
  views/notes/<UUID>.md     Per-record Markdown snapshots
```

Originals use `.bin` names to reduce active-content handling in the viewer. Their original filenames are preserved in metadata and download links. Windows permissions inherit from the selected directory; the deployment must restrict access to the intended local account.

## Save a fact

Pass a UTF-8 JSON file to `remember --record FILE`, or use `--record -` to read JSON from standard input. Pass text as data, not interpolated shell code.

```json
{
  "category": "habits",
  "title": "Answer style",
  "body": "The user prefers a short summary before implementation details.",
  "kind": "fact",
  "source": {
    "channel": "feishu",
    "ref": "synthetic:tenant:bot:chat:message-001",
    "speaker": "local-owner",
    "observed_at": "2026-10-19T00:00:00Z"
  },
  "tags": ["communication"],
  "event_id": "synthetic:tenant:bot:chat:message-001:answer-style"
}
```

```sh
python3 koder-personal-knowledge/scripts/knowledge.py \
  --principal local-owner remember --record examples/preference.json
```

| Field | Meaning |
| --- | --- |
| `category` | One of `profile`, `habits`, `people`, `tools`, `work`, `industry`, `life`, `reference`. |
| `title` / `body` | A useful, focused record. Title limit: 240 characters. Body limit: 256K characters. |
| `kind` | `fact`, `inference`, or `reference`. Defaults to `fact`. |
| `source` | Required `channel` and `ref`; optional `speaker`, `observed_at`, and `extractor`. |
| `confidence` | A number from 0 to 1. Defaults to 1 for facts/references, 0.5 for inferences. |
| `tags` | Up to 24 short labels. |
| `event_id` | Optional stable key for retry deduplication. |
| `supersedes` | Optional ID of a current record in the same space to replace. Owner only. |

The host should construct `event_id` from the channel, binding, conversation, message, and extracted fact key. Multiple facts from one message need distinct fact keys. Repeating the same event and payload returns its original ID. Reusing the event with changed content returns `EVENT_CONFLICT`.

Use `kind=inference` for a hypothesis about a preference. It receives `unconfirmed` status and is excluded from normal search. Confirmation or correction is a new fact with `supersedes` pointing to the earlier ID. The older record becomes `superseded` and remains available for inspection.

Do not include keys, tokens, passwords, authentication headers, or credentials in `source` or any record field. The script rejects recognizable secret patterns without echoing their values.

## Search and read

```sh
python3 koder-personal-knowledge/scripts/knowledge.py \
  --principal local-owner search "summary" --limit 8 --max-chars 6000

python3 koder-personal-knowledge/scripts/knowledge.py \
  --principal local-owner list --offset 0 --limit 50

python3 koder-personal-knowledge/scripts/knowledge.py \
  --principal local-owner get ENTRY_ID --offset 0 --max-chars 1000
```

`search` returns current facts/references and bounded excerpts with provenance. `--include-unconfirmed` adds inferences. Superseded entries stay out of search. Matching uses keywords and Chinese text fragments, not embeddings. Try a domain term or another phrase when a natural-language question misses.

The search budget includes its serialized JSON fields; defaults are eight results and 6,000 characters. Limits are 30 results and 24,000 characters. Queries are limited to 800 characters. Provenance in a search excerpt may be shortened; use `get` for the stored record.

`get` returns a page of body text, defaulting to 6,000 characters, plus metadata. Follow `next_offset` until it is `null` to read the remaining pages. Its `--max-chars` limit applies to the body; account for metadata when building a model prompt. `list` is a paginated inspection API and includes full stored records, so the host should not send its complete output to the model by default.

## Archive a file

```sh
python3 koder-personal-knowledge/scripts/knowledge.py \
  --principal local-owner import-file \
  --file examples/field-notes.txt --source examples/file-source.json
```

The source file stays in place. The tool stores a managed copy and its SHA-256 hash. It rejects files larger than 32 MiB. Text formats support UTF-8 and GB18030; large text should be split into focused records.

For a PDF, Office file, image, or other binary, first use an available host parser/OCR tool. Save its real output as UTF-8, then pass it to the archive command:

```sh
python3 koder-personal-knowledge/scripts/knowledge.py \
  --principal local-owner import-file \
  --file ./report.pdf --source ./source.json --extracted-text ./report.txt
```

`source.json` uses the same fields as a record's source object. Put the parser name/version in `source.extractor`. Extraction states are `text`, `host_extracted_text`, or `attachment_only`. The last means the original is present but its contents are not indexed. Bind extracted text to the actual original; the script cannot verify what an external parser read.

Common credential files, including `.env`, `.pem`, `.key`, `.p12`, `.pfx`, and `.kdbx`, are refused. Secret detection cannot reliably inspect every binary format; the host must still screen selected material.

## Spaces and group access

Initialization creates the `personal` space, accessible only to the owner. The owner can add a project space or share an existing space with a verified group principal.

```sh
python3 koder-personal-knowledge/scripts/knowledge.py \
  --principal local-owner create-space project-a --title "Project A"

python3 koder-personal-knowledge/scripts/knowledge.py \
  --principal local-owner --space personal \
  grant --member group:feishu:tenant:chat --role reader

python3 koder-personal-knowledge/scripts/knowledge.py \
  --principal group:feishu:tenant:chat --space personal search "delivery"

python3 koder-personal-knowledge/scripts/knowledge.py \
  --principal local-owner --space personal \
  grant --member group:feishu:tenant:chat --role revoke
```

`reader` can retrieve. `writer` can also add records and files. Only the owner changes grants, deletes, supersedes facts, or renders the whole library. Record a contributor as the actual speaker; their statements do not automatically become facts about the owner.

The host authenticates group membership and supplies the effective group principal. These strings are not authentication tokens. A denied request must not be retried under the owner principal.

## Inspect, forget, and rebuild

```sh
python3 koder-personal-knowledge/scripts/knowledge.py --principal local-owner render
python3 koder-personal-knowledge/scripts/knowledge.py --principal local-owner forget ENTRY_ID
```

The owner-wide HTML view includes every space, unconfirmed inference, and superseded record. Do not publish it or send it into a group. Share authorized excerpts or selected files through the host instead.

`forget` removes a record, its generated note/view content, and any original copy no other record uses. A tombstone retains only the ID, deletion time, and an event hash to block automatic resurrection through an identical event retry. To forget a topic, delete all its versions and duplicate references, not just the newest fact.

Original source files, messages in connected apps, external backups, and OS snapshots are separate. Physical erasure from storage media is not guaranteed.

SQLite is authoritative. HTML/JSON/Markdown views can be stale or inconsistent after an interrupted write; run `render` after recovery. Back up while no writes are active, or use a SQLite-aware backup and copy the associated files. Avoid ordinary cloud-folder synchronization of a database that multiple machines are writing.

## Exit codes and recovery

| Code | Meaning | Next step |
| --- | --- | --- |
| `0` | Operation completed. | Use the actual returned result. |
| `2` | Controlled input, access, or state error. | Read the error code and correct the request. |
| `3` | Local filesystem/database error. | Check permissions, available space, or file locks. |

Common state errors include `NOT_INITIALIZED`, `OWNER_MISMATCH`, `EVENT_CONFLICT`, `EVENT_FORGOTTEN`, and `ACCESS_DENIED`. Writes have an eight-second lock wait. The tool never escalates OS privileges or silently switches storage locations.
