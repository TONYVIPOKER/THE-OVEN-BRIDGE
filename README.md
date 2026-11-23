# THE OVEN BRIDGE — read-only handshake v1

A limited GitHub Issues polling worker for THE OVEN. This repository contains **no Hermes executor integration yet**.

## Security first

**This repository must be PRIVATE before starting the worker.** The worker checks GitHub's repository visibility at startup and refuses to run against a public repository.

Never commit credentials, local music projects, sensitive logs, environment variables, private paths, or detailed device diagnostics. Issue contents are untrusted. The worker only accepts one hardcoded operation and does not invoke shells or DAW controls.

## Protocol

Title: `[THE-OVEN TASK] status.readonly.v1`

Issue body (example; generate a fresh UUID and current UTC timestamp each time):

```json
{
  "protocol": "the-oven-bridge/v1",
  "task_id": "5bfb73e9-8fde-40bb-a998-1caa80e05a9f",
  "operation": "status.readonly.v1",
  "arguments": {},
  "dry_run": true,
  "created_at_utc": "2026-11-23T07:30:00Z"
}
```

Worker checks fixed repository identity, issue creator allowlist, exact schema, timestamp freshness (+/- 1 hour), UUID validity, operation allowlist and one-time processing. The result is a short, sanitized GitHub issue comment. No raw logs leave the PC.

## Install on MIND-BLOWING-PC (after making repository private)

Requires Python 3.10+ and Git. The following commands are **instructions for the user or an authorized local executor**; this GitHub commit does not run them:

1. Clone this repository to a local directory of your choosing.
2. Run `python -m unittest discover -s tests -v` and require all tests to pass.
3. Create a **fine-grained GitHub token** scoped only to this private repository, with Issues read/write and repository Metadata read. Never put the token in an issue or source file.
4. Set environment variables locally in the worker process:
   - `OVEN_BRIDGE_GITHUB_TOKEN` — secret token.
   - `OVEN_BRIDGE_ALLOWED_AUTHORS` — `TONYVIPOKER`.
   - `OVEN_PROJECT_ROOT` — local THE OVEN project root; omit for a configuration-only check.
5. Run `python worker.py` in a terminal with those environment variables available.
6. Create an issue following the schema above with a new task ID and fresh UTC timestamp, then watch for a `THE-OVEN-BRIDGE-RESULT` comment on the same issue.

The worker polls every 20 seconds and keeps a local SQLite record of task IDs for duplicate suppression. It is intentionally a foreground, read-only diagnostic probe; no service install, autostart, or Hermes control is included.

**Limitations:** The worker reports only whether the configured project directory and three canonical documentation files exist. It cannot prove that Hermes, Ableton, Virtual Ear, or an autonomous learning loop are healthy. Issue comments are not verified Hermes acknowledgements.

## Next stage — only after the handshake

Implement a separately authenticated and reviewed local Hermes adapter. Require operation-specific authorization, audit trails, bounded runtime, one execution ID per action and rollback gates. Never turn this issue queue into a generic remote shell.
