"""Publication contract tests; no GitHub credentials or network required."""
import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("uem_import", ROOT / "scripts/import_completed_submission.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    record = {"version": 1, "category": "career", "author": "张同学", "year": "2026",
              "destination": "某企业", "program": "产品经理", "body": "## 我的经历\n\n具体经历。",
              "contact": ""}
    payload = base64.urlsafe_b64encode(json.dumps(record, ensure_ascii=False).encode()).decode().rstrip("=")
    issue = {"number": 57, "title": "[飞跃手册投稿] [就业] 张同学 — 某企业 · 产品经理",
             "state_reason": "completed", "labels": [{"name": "submission:pending"}],
             "body": "### 经历\n\n<!-- uem-submission-v1:" + payload + " -->"}
    return {"action": "closed", "sender": {"login": "FuTseYi"},
            "repository": {"full_name": "UEM-Feiyue/UEM-Feiyue.github.io"}, "issue": issue}


class PublicationTests(unittest.TestCase):
    def test_import_idempotent_and_safe(self):
        event = fixture()
        with tempfile.TemporaryDirectory() as directory:
            path, created = module.import_event(event, Path(directory))
            self.assertTrue(created)
            self.assertEqual(path.name, "issue-57.md")
            self.assertIn("source_issue: 57", path.read_text())
            self.assertIn("## 我的经历", path.read_text())
            self.assertFalse(module.import_event(event, Path(directory))[1])

    def test_only_maintainer_completed_closure(self):
        for edit in (lambda x: x.update(action="reopened"),
                     lambda x: x["issue"].update(state_reason="not_planned"),
                     lambda x: x["sender"].update(login="someone-else"),
                     lambda x: x["repository"].update(full_name="other/repo"),
                     lambda x: x["issue"].update(title="not a submission"),
                     lambda x: x["issue"].update(labels=[]),
                     lambda x: x["issue"].update(body="invalid")):
            event = fixture()
            edit(event)
            with self.subTest(event=event), self.assertRaises(ValueError):
                with tempfile.TemporaryDirectory() as directory:
                    module.import_event(event, Path(directory))

    def test_unsafe_marker_and_yaml_are_rejected_or_quoted(self):
        event = fixture()
        event["issue"]["title"] = event["issue"]["title"].replace("某企业", "其它企业")
        with self.assertRaises(ValueError):
            module.decode_issue(event["issue"])
        event = fixture()
        event["issue"]["body"] += "\n" + event["issue"]["body"]
        with self.assertRaises(ValueError):
            module.decode_issue(event["issue"])


if __name__ == "__main__":
    unittest.main()
