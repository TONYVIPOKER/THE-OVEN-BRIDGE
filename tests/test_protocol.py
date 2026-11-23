"""Unit tests for the read-only protocol. Run: python -m unittest discover -s tests -v"""
import datetime as dt
import json
import unittest
import uuid
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import worker


def make_issue(**overrides):
    msg = {
        "protocol": worker.PROTOCOL,
        "task_id": str(uuid.uuid4()),
        "operation": worker.OPERATION,
        "arguments": {},
        "dry_run": True,
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    msg.update(overrides)
    return {"title": worker.TITLE, "user": {"login": "TONYVIPOKER"},
            "body": json.dumps(msg), "number": 1}


class ProtocolTests(unittest.TestCase):
    def test_accept_valid_readonly_task(self):
        self.assertIsNotNone(worker.validate_issue(make_issue(), {"tonyvipoker"}))

    def test_reject_arbitrary_operation(self):
        self.assertIsNone(worker.validate_issue(make_issue(operation="shell.execute"), {"tonyvipoker"}))

    def test_reject_command_arguments(self):
        self.assertIsNone(worker.validate_issue(
            make_issue(arguments={"command": "echo hello"}), {"tonyvipoker"}))

    def test_reject_untrusted_author(self):
        self.assertIsNone(worker.validate_issue(make_issue(), {"somebody-else"}))

    def test_reject_expired_task(self):
        stamp = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2)).isoformat()
        self.assertIsNone(worker.validate_issue(
            make_issue(created_at_utc=stamp), {"tonyvipoker"}))

    def test_reject_unexpected_fields(self):
        self.assertIsNone(worker.validate_issue(
            make_issue(extra="unexpected"), {"tonyvipoker"}))

    def test_reject_pull_request(self):
        issue = make_issue()
        issue["pull_request"] = {"url": "https://example.org"}
        self.assertIsNone(worker.validate_issue(issue, {"tonyvipoker"}))


if __name__ == "__main__":
    unittest.main()
