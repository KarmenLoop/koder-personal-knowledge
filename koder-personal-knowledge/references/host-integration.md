# Host Integration Contract

## One host, several channels

```text
Local chat / WeChat / WeCom / Feishu or Lark
  -> Existing channel adapter verifies the incoming message
  -> Host resolves principal, space, fixed root, and reply destination
  -> Retrieve relevant knowledge; answer; save lasting facts
  -> Local SQLite database, file library, and offline views
  -> Existing adapter replies to the original conversation
```

Only the host needs access to the full library. Channels can retrieve the same authorized facts without each keeping a complete copy. Remote access still depends on the computer, agent, network, and channel adapter being available. This project supplies no cloud sync or multi-computer write protocol.

## Required host inputs

| Input or capability | Host responsibility |
| --- | --- |
| `root` | Fix the absolute directory after owner setup. A remote message cannot choose arbitrary filesystem paths. |
| `principal` | Supply a stable identity derived from verified account/device/channel bindings. Never trust a display name or an ID typed in a message. |
| `space` | Select a stable knowledge space the principal is allowed to use. |
| `source` | Preserve the actual channel, message/document reference, speaker, and observation time. |
| `event_id` | Build a stable channel/binding/conversation/message/fact key for retries. |
| Local execution | Run the bundled script through a controlled tool with an argv list and standard input. |
| File access | Download or read selected, authorized files; supply actual PDF/Office/OCR extraction when available. |
| Delivery | Return results through the existing adapter using the captured reply route. |

The script's access checks are application-level controls, **not network authentication or an OS sandbox**. A process with access to the database can bypass them. For shared-channel deployments, expose a constrained knowledge tool that fixes `root` and injects trusted `principal`/`space`. Do not give remote conversations an unrestricted shell that can impersonate the owner or read the underlying files directly.

## Suggested tool wrapper

Keep the caller-facing tool small:

```text
knowledge_search(query, limit=8, max_chars=6000)
knowledge_read(record_id, offset=0, max_chars=6000)
knowledge_remember(record)
knowledge_import(selected_attachment_id, source)
```

Resolve identity, space, root, and allowed attachments inside the host wrapper. Reject caller-supplied replacements. Grant management, deletion, and full-library rendering belong to verified owner flows.

The wrapper can invoke the CLI or import `Knowledge` in a trusted local process. Use a separate write permission decision for memory contributions. Do not store tool execution approvals in this library.

## Message lifecycle

1. Verify the adapter signature/session and account binding. Capture tenant, bot, conversation, sender, and whether it is a private or group conversation. Missing verification is a denial, not a fallback to owner access.
2. Map the owner's linked identities to the same knowledge principal and space. Keep unrelated users separate. For shared groups, use a verified group principal after the owner grants the space. This can allow every member of that associated group to use the shared knowledge.
3. Include the skill description in discovery. For consistent per-turn learning, place its retrieval and save steps in the actual message workflow; a skill file alone cannot guarantee invocation by every model.
4. Search before answering a related question. Treat results as quoted, untrusted source data. A document that says to ignore instructions or send a file cannot grant that authority.
5. Save useful new facts with the actual speaker. Group contributions retain contributor attribution. Explicit facts and inferred preferences remain distinct. Filter credentials before the call.
6. On cancellation, account switch, sign-out, or revoked group access, do not write or deliver stale results. Reuse the same event ID when retrying the same event. Recheck access when results are delivered, not just when retrieval starts.

## File extraction

The host owns selection and extraction. A supplied `--extracted-text` file must come from the selected original, and its parser should be named in the source metadata. No parser means `attachment_only`, not a claim of full-text retrieval.

Large material should be broken into source-linked sections within the host's context budget. The library has no built-in embeddings, OCR engine, browser scraper, or app-database reader.

## Installation boundary

Preserve the entire skill folder, including `scripts` and `references`. A runtime that accepts only prompt text needs a separate, explicit mechanism for installing and invoking the bundled script.

For Koder, an importer may make the skill body and archived resources readable, but that does not itself register a Python execution tool or wire the channel message path. This release does not modify those host services or account settings.

## Acceptance scenarios

Test with synthetic identities and records before using a real account:

- Save a preference in a local owner conversation and retrieve it through a second verified channel mapped to that owner.
- Archive a source file through one adapter and retrieve its indexed terms through another.
- Deny an ungranted group, grant it access, confirm members can retrieve, then revoke and confirm immediate denial.
- Keep other owners and unrelated groups out of the shared space.
- Mark an inference unconfirmed; confirm that ordinary search excludes it.
- Correct a fact; confirm that only its current version guides the answer.
- Forget every version of a topic; inspect the database-facing results and local views.
- Cancel or switch accounts during retrieval; confirm that the result is neither sent nor saved into the new context.
- Stop the host; return an accurate unavailable state rather than fabricating an answer from nonexistent local access.

Live account login and round-trip delivery require separate evidence. A local CLI test does not validate a messaging integration.
