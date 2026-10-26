# Koder Personal Knowledge: from download to first save and search

English | [简体中文](tutorial.zh-CN.md) · [Project](../README.md)

This guide matches **v1.0.0**. It extracts the practice path from the README into install → first task → channels/docs → troubleshoot → update/remove.

## 1. Download and install

Requirements: **Python 3.9+** including standard `sqlite3`. No third-party packages.

1. Download the installable skill ZIP from [Releases](https://github.com/KarmenLoop/koder-personal-knowledge/releases), or clone / Download ZIP for full source and tests.
2. Keep the complete `koder-personal-knowledge/` folder (script + reference docs).
3. Import the entire skill folder with the host’s installer, or place it in the host’s configured skills directory.
4. Expose the bundled Python script through a **controlled local tool**.
5. Have the host supply a fixed library root and a **verified** principal and space on each call.
6. Enable automatic skill selection; for consistent per-turn learning, wire retrieval and save into the host message flow.

There is no desktop installer, model bundle, or channel login service in this repository. Importing a Markdown skill does not create a background worker or connect a messaging account.

## 2. First task (local helper, no host required)

Use an isolated directory and a synthetic owner for practice. A deployed host should use its own verified, stable owner ID. On Windows, use `python` instead of `python3` if needed.

```sh
# Inspect the platform default location without creating anything.
python3 koder-personal-knowledge/scripts/knowledge.py path

# Create a separate library for this walkthrough.
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge init --owner local-owner

# Save an example preference with its source.
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner \
  remember --record examples/preference.json

# Retrieve within a small response budget.
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner \
  search "summary" --max-chars 2000

# Archive a selected text file and its contents.
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner \
  import-file --file examples/field-notes.txt --source examples/file-source.json

# Rebuild local views and print their location.
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner render
```

Open `demo-knowledge/views/index.html` in a browser. The page works offline and includes the whole library—keep it on the owner’s computer.

**PowerShell (single-line style):**

```powershell
$Script = ".\koder-personal-knowledge\scripts\knowledge.py"
python $Script --root .\demo-knowledge init --owner local-owner
python $Script --root .\demo-knowledge --principal local-owner remember --record .\examples\preference.json
python $Script --root .\demo-knowledge --principal local-owner search "summary" --max-chars 2000
python $Script --root .\demo-knowledge --principal local-owner import-file --file .\examples\field-notes.txt --source .\examples\file-source.json
python $Script --root .\demo-knowledge --principal local-owner render
```

Count accessible records without returning note bodies:

```sh
python3 koder-personal-knowledge/scripts/knowledge.py --root ./demo-knowledge --principal local-owner stats
```

Add `--space SPACE_ID` before `stats` for a shared space. Corrections, sharing, defaults, and errors: [commands.md](../koder-personal-knowledge/references/commands.md).

### Default roots

| Platform | Default |
| --- | --- |
| Windows with D: | `D:\KoderKnowledge` |
| Windows without D: | `KoderKnowledge` in the user profile |
| macOS / Linux | `~/KoderKnowledge` |

`--root` or `KODER_KNOWLEDGE_ROOT` selects another location. After init, persist the absolute path. Switching path does not migrate; an unwritable D: is reported rather than silently creating a second library.

## 3. Channels, sharing, and documents

- Host must authenticate inbound messages and map linked accounts to a verified principal.
- Owner can share a space with a verified group principal (`reader` / `writer`). Only the owner changes grants, deletes, supersedes, or renders the full library.
- Knowledge access ≠ permission to run computer tasks or send files to a new recipient.
- UTF-8 / GB18030 text indexes directly. PDF/Office/images archive as originals; searchable text needs host parser/OCR. `attachment_only` ≠ searchable text.
- Limits: 32 MiB per original, 256K characters per record. Keyword / Chinese-fragment retrieval; no vector search.
- Before hosted models or shared channels: [privacy.md](privacy.md). Integration inputs: [host-integration.md](../koder-personal-knowledge/references/host-integration.md).

## 4. Troubleshoot

- **Command JSON error / bad exit:** Check root, initialized owner, verified principal, and space grant ([commands](../koder-personal-knowledge/references/commands.md)).
- **PDF imported but not in text search:** Likely `attachment_only`—run host parser/OCR and supply extracted text.
- **Originals end in `.bin`:** Managed copies use inert extensions; metadata keeps the original name.
- **Phone cannot see library:** Host must be running and channel connected; this repo is not a relay.
- **Group saw private facts:** Review explicit space grants; revoke to stop future tool access ([faq](faq.md)).
- **Permission / lock / disk errors:** Check OS permissions, free space, and concurrent writers.

## 5. Update, roll back, or remove

1. Back up the **full** library (SQLite-aware method + referenced files)—do not copy only a live main DB file.
2. Read [CHANGELOG.md](../CHANGELOG.md) for the target version.
3. Validate upgrade or rollback on a **copy** first. Changing `--root` is not a migration.
4. Replace the skill folder with the new release; keep the library path stable unless you intentionally migrate.
5. Removing the skill does **not** automatically delete an external knowledge library. To forget content, use the deletion flows in the command reference, then check generated views and retained backups.

## 6. Development check

```sh
python3 -B -m unittest discover -s tests -v
```

Tests use synthetic data in temporary directories. They do not open your personal library, connect messaging, or call a paid API. Local macOS green does not certify native Windows/Linux or hosted CI by itself ([validation](validation.md)).

[Project home](../README.md) · [简体中文教程](tutorial.zh-CN.md)
