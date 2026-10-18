# Validation and Current Limits

## Local results

The English release was checked on macOS with Python 3.9.6 using synthetic data only.

| Check | Result |
| --- | --- |
| Full local regression suite | 25 tests passed, exit 0. |
| Concurrent writes | Four real subprocess writers retained all records. |
| Default path rules | D: preference, C: fallback, redirected Windows profiles, and macOS/Linux paths checked as path logic. |
| Record lifecycle | Persistence, event retries/conflicts, correction history, inference exclusion, deletion, and tombstone retry prevention checked. |
| Access | Unrelated principals/spaces denied; a verified group grant allowed retrieval; revocation denied later access. |
| Files and views | Original copy/hash, text retrieval, unextracted binary status, view escaping, symlink rejection, and deletion cleanup checked. |
| Context handling | Search result budget and lossless paged body retrieval checked. |
| English presentation | Skill, documentation, CLI help, generated labels, and examples reviewed in English. |
| English walkthrough | 10 actual CLI subprocess calls passed, including an expected access-denied result after revocation. |

Run the same local suite from the repository root:

```sh
python3 -B -m unittest discover -s tests -v
```

The tests include synthetic Unicode fixtures for multilingual matching. Source escapes preserve those fixtures without making the documentation language-dependent. The Windows symlink case skips only when that account lacks symlink creation privileges.

## Reproducible walkthrough

```sh
python3 -B tools/smoke.py
python3 -B tools/build_release.py
```

The walkthrough creates a temporary library, saves an example preference, retrieves it, imports the example reference file, shares a space with a synthetic group, verifies access, revokes it, and verifies denial. It also checks the English offline view and the CLI's JSON results. It does not read a real user's library or contact a messaging service.

The packaging tool creates a skill ZIP with its script, references, metadata, and license notices, plus a SHA-256 checksum. It excludes databases, managed files, generated owner views, and machine-specific validation logs.

## Not established by these checks

- Native Windows drive permissions and actual D:/C: volume behavior.
- A native Linux installation or hosted CI matrix.
- Real WeChat, WeCom, or Feishu account authentication and round-trip delivery.
- A host model automatically invoking the skill on each relevant turn.
- External PDF, Office, image, audio, or OCR extraction.
- Cloud synchronization, multiple computers writing one library, or remote relays.
- OS encryption, full-disk erasure, or a sandbox against processes running as the same local user.

Local unit tests and a CLI walkthrough do not substitute for those checks. Host integrators should record their own platform, account, cancellation, and delivery results before advertising a completed integration.
