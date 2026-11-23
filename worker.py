#!/usr/bin/env python3
"""THE OVEN Bridge v1: constrained, read-only GitHub Issues worker.
Python 3.10+, standard library only. No arbitrary commands are executed.
"""
import datetime as dt
import json
import os
from pathlib import Path
import sqlite3
import time
import urllib.error
import urllib.request

REPO = "TONYVIPOKER/THE-OVEN-BRIDGE"
TITLE = "[THE-OVEN TASK] status.readonly.v1"
PROTOCOL = "the-oven-bridge/v1"
OPERATION = "status.readonly.v1"
API = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github+json",
           "X-GitHub-Api-Version": "2022-11-28"}


def request(method, endpoint, payload=None):
    token = os.environ["OVEN_BRIDGE_GITHUB_TOKEN"]
    headers = {**HEADERS, "Authorization": "Bearer " + token}
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(API + endpoint, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def validate_issue(issue, authors):
    if issue.get("title") != TITLE or "pull_request" in issue:
        return None
    if issue.get("user", {}).get("login", "").lower() not in authors:
        return None
    try:
        message = json.loads(issue["body"])
    except (ValueError, KeyError, TypeError):
        return None
    if not isinstance(message, dict) or set(message) != {
        "protocol", "task_id", "operation", "arguments", "dry_run", "created_at_utc"
    }:
        return None
    if message["protocol"] != PROTOCOL or message["operation"] != OPERATION:
        return None
    if message["arguments"] != {} or message["dry_run"] is not True:
        return None
    import uuid
    try:
        uid = str(uuid.UUID(message["task_id"]))
    except (ValueError, TypeError, AttributeError):
        return None
    if uid != message["task_id"]:
        return None
    try:
        stamp = dt.datetime.fromisoformat(message["created_at_utc"].replace("Z", "+00:00"))
        if stamp.tzinfo is None or abs((utc_now() - stamp).total_seconds()) > 3600:
            return None
    except (TypeError, ValueError, AttributeError):
        return None
    return message


def status_probe():
    """Only coarse booleans. Never return private filenames, paths or logs."""
    root_text = os.environ.get("OVEN_PROJECT_ROOT", "")
    if not root_text:
        return {"configuration_present": False, "project_directory_present": False,
                "canonical_documents_present": False}
    root = Path(root_text)
    return {
        "configuration_present": True,
        "project_directory_present": root.is_dir(),
        "canonical_documents_present": all(
            (root / "knowledge" / name).is_file()
            for name in ("START_HERE.md", "CANONICAL_MODULE_MAP.md",
                         "LIVE_CONTINUITY_CHECKPOINT.md")
        ),
    }


def main():
    token = os.environ.get("OVEN_BRIDGE_GITHUB_TOKEN")
    authors = {x.strip().lower() for x in
               os.environ.get("OVEN_BRIDGE_ALLOWED_AUTHORS", "").split(",") if x.strip()}
    if not token or not authors:
        raise SystemExit("Set OVEN_BRIDGE_GITHUB_TOKEN and OVEN_BRIDGE_ALLOWED_AUTHORS")
    repo = request("GET", "/repos/" + REPO)
    if repo.get("private") is not True or repo.get("full_name", "").lower() != REPO.lower():
        raise SystemExit("Refusing to run: expected PRIVATE repository with correct identity")
    # Never store execution history in the repository. Keep it local.
    db_file = Path.home() / ".the_oven_bridge_tasks.sqlite3"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE IF NOT EXISTS tasks (task_id TEXT PRIMARY KEY, issue_number INTEGER, state TEXT)")
    conn.commit()
    print("Bridge worker ready (read-only status probe only).", flush=True)
    while True:
        try:
            issues = request("GET", "/repos/" + REPO +
                             "/issues?state=open&per_page=40&sort=created&direction=desc")
            for issue in reversed(issues):
                task = validate_issue(issue, authors)
                if task is None:
                    continue
                key = task["task_id"]
                if conn.execute("SELECT 1 FROM tasks WHERE task_id=?", (key,)).fetchone():
                    continue
                # Persist before acting to prevent duplicate processing on restart.
                conn.execute("INSERT INTO tasks VALUES (?, ?, ?)",
                             (key, issue["number"], "claimed"))
                conn.commit()
                result = status_probe()
                envelope = {
                    "protocol": PROTOCOL,
                    "task_id": key,
                    "operation": OPERATION,
                    "state": "succeeded",
                    "worker_version": "1.0.0",
                    "timestamp_utc": utc_now().isoformat(),
                    "result": result,
                    "limitations": "Local filesystem probe only; not Hermes execution or Ableton health."
                }
                try:
                    request("POST", "/repos/" + REPO + "/issues/" +
                            str(issue["number"]) + "/comments",
                            {"body": "THE-OVEN-BRIDGE-RESULT\n" +
                             "```json\n" + json.dumps(envelope, indent=2) + "\n```"})
                    conn.execute("UPDATE tasks SET state='reported' WHERE task_id=?", (key,))
                    conn.commit()
                    print("Reported task", key, flush=True)
                except Exception:
                    print("Result delivery failed; task retained for manual review.", flush=True)
            time.sleep(20)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            print("GitHub unavailable; retrying.", flush=True)
            time.sleep(60)


if __name__ == "__main__":
    main()
