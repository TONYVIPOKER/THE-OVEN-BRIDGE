# THE OVEN BRIDGE

A minimal GitHub Issues task queue specification for the THE OVEN / Hermes integration.

## Security boundary

This repository may be public. Never post tokens, credentials, local computer paths, machine fingerprints, private logs, music files, or unrestricted commands.

GitHub issues are **requests**, not authorization to run arbitrary code. The local Hermes bridge worker MUST authenticate to GitHub, verify repository and issue author against an explicit allowlist, validate the task against a fixed operation registry, and reject unsupported inputs. No shell commands, PowerShell text, scripts, URLs, executable code, or filesystem paths may be passed as task arguments.

## Request protocol (version 1)

Create a GitHub issue with this title:

`[THE-OVEN TASK] status.readonly.v1`

Body:

```json
{
  "protocol": "the-oven-bridge/v1",
  "task_id": "<unique UUID>",
  "operation": "status.readonly.v1",
  "arguments": {},
  "dry_run": true
}
```

The worker accepts tasks **only** after locally verifying the repository owner, authorized issue creator, JSON schema, expiration, a unique task ID, and matching fixed operation. It must independently authorize execution even for read-only tasks. Unknown tasks are ignored. GitHub issue labels and content must never be trusted as authentication.

## Acknowledgement/result protocol

The worker posts an issue comment containing a JSON status envelope with `protocol`, `task_id`, `worker_version`, `state` (accepted/running/succeeded/failed/rejected), `timestamp_utc`, and a small sanitized `result`. Keep raw logs on the PC. Include no user-identifying system information. Record task IDs locally for idempotent execution.

## First test

Only permit `status.readonly.v1` initially. It returns a small generic health result after local confirmation that THE OVEN's status probe exists. The worker must not infer success from issue creation or GitHub connectivity.

## Deployment gate

This repo defines the protocol but **does not install or start a local worker**. A separately reviewed, authenticated local worker must be installed and tested before claiming end-to-end Hermes connectivity. Prefer a private repository, limited-scope GitHub credentials, and least-privilege permissions.
