# Frequently Asked Questions

## Is this a chatbot or a model?

It is a portable agent skill with a local knowledge tool. Your host provides the model, conversation interface, account identity, and any messaging connections.

## Does it learn immediately?

An empty library can be used right away. The skill tells an agent to save useful, lasting facts during conversation. Consistent per-turn learning requires the host to run that workflow; a skill file does not create an always-on process by itself.

## Does it change model weights?

No. Learning here means keeping inspectable records and retrieving them later. Model fine-tuning is not part of the project.

## Can my phone use the knowledge on my computer?

Yes, through a running host agent and an already-connected channel adapter. The host verifies the request, retrieves authorized knowledge, and replies through that app. This repository does not provide remote access, an app login, or a relay service on its own.

## Can WeChat, WeCom, and Feishu use the same knowledge?

They can when the host maps the linked identities to the same authorized principal and space. Display names alone cannot establish that relationship. Live account round trips still need validation in the host product.

## Can everyone in a group use memory from a private conversation?

The owner can explicitly share that space with a verified group principal, allowing members to use it through the host. Other people's unrelated private spaces remain separate. Revoke the grant to stop future tool access; the host must also cancel or deny stale results.

## Does it sync across computers?

Not in this release. Several channels can use one host, but multi-computer synchronization requires a separate protocol. Do not rely on ordinary cloud-folder sync for a SQLite database being written on multiple machines.

## Is the library encrypted?

The tool does not implement encryption at rest. Protect it through your local account, directory permissions, and suitable disk encryption. The script's principal strings are not a replacement for host authentication.

## Why did a PDF import without appearing in text search?

The original may be archived as `attachment_only`. Have the host run an actual parser or OCR tool and provide its extracted text when importing. The tool has no built-in PDF/Office/OCR engine.

## Why do original files end in `.bin`?

Managed copies use content hashes and inert extensions to reduce active-content handling in the viewer. Metadata and download links retain the original name. The original input file is unchanged.

## What happens when I correct or delete a fact?

Correction marks the old version superseded and saves a new version with a source. Deletion removes the selected record and its generated views. For a whole topic, delete the older versions and duplicates too. External backups and source messages are separate.

## Can this solve every context-limit error?

It provides bounded search results and paged reads so the host can include less history. The host still needs to manage the model's real token window, tool output, and total prompt. This project does not change a provider's limits or repair an API connection.

## Where should I start when a command fails?

Read its JSON error and exit code. Check that the root is correct, the owner was initialized, the principal was verified, and the space was granted. For local IO failures, check permissions, disk space, and file locks. See the [command reference](../koder-personal-knowledge/references/commands.md).
