"""Publication contract tests; no GitHub credentials or network required."""
import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("uem_import", ROOT / "scripts/import_completed_submission.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PEM = KEY.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()


def fixture():
    record = {"version": 1, "category": "career", "author": "张同学", "year": "2026", "college": "某学院", "major": "某专业",
              "destination": "某企业", "program": "产品经理", "body": "## 我的经历\n\n具体经历。",
              "contact": "", "institution_type": ""}
    payload = base64.urlsafe_b64encode(json.dumps(record, ensure_ascii=False).encode()).decode().rstrip("=")
    signature = KEY.sign(module.SIGNING_CONTEXT + payload.encode(), padding.PKCS1v15(), hashes.SHA256())
    signed = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    issue = {"number": 57, "title": "[飞跃手册投稿] [就业] 张同学 — 某企业 · 产品经理",
             "state_reason": "completed", "labels": [{"name": "submission:pending"}],
             "body": "### 经历\n\n<!-- uem-submission-v2:" + payload + ":" + signed + " -->"}
    return {"action": "closed", "sender": {"login": "FuTseYi"},
            "repository": {"full_name": "UEM-Feiyue/UEM-Feiyue"}, "issue": issue}


class PublicationTests(unittest.TestCase):
    def test_versioned_admission_and_signed_publication(self):
        from scripts import build
        event = fixture()
        record = module.decode_issue(event["issue"], PEM)
        self.assertEqual(record["version"], 1)
        record.pop("institution_type")
        record.update(version=2, category="kaoyan", destination="北京理工大学", institution_id="bit",
                      admission_year="2026", degree_type="academic", admission_method="exam")
        self.assertEqual(module.validate_record(record)["institution_id"], "bit")
        for edit in ({"program": ""}, {"admission_year": ""}, {"institution_id": "missing"}):
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                module.validate_record(dict(record, **edit))
        encoded = base64.urlsafe_b64encode(json.dumps(record).encode()).decode().rstrip("=")
        signature = KEY.sign(module.SIGNING_CONTEXT + encoded.encode(), padding.PKCS1v15(), hashes.SHA256())
        signed = base64.urlsafe_b64encode(signature).decode().rstrip("=")
        event["issue"]["body"] = "<!-- uem-submission-v2:" + encoded + ":" + signed + " -->"
        event["issue"]["title"] = "[飞跃手册投稿] [考研] 张同学 — 北京理工大学 · 产品经理"
        with tempfile.TemporaryDirectory() as directory:
            path, _ = module.import_event(event, Path(directory), PEM)
            meta, body = build.parse(path)
            self.assertEqual(meta["institution_id"], "bit")
            self.assertIn("双一流 · 自划线", build.render(meta, body, "articles/test.html"))

    def test_reviewed_commit_triggers_source_publication(self):
        workflow = (ROOT / '.github/workflows/publish-completed-submission.yml').read_text(encoding='utf-8')
        deploy = (ROOT / '.github/workflows/deploy.yml').read_text(encoding='utf-8')
        self.assertIn('permission-contents: write', workflow)
        self.assertIn('git push origin HEAD:main', workflow)
        self.assertNotIn("vars.PUBLISH_APP_ID != ''", workflow + deploy)

    def test_import_idempotent_and_safe(self):
        event = fixture()
        with tempfile.TemporaryDirectory() as directory:
            path, created = module.import_event(event, Path(directory), PEM)
            self.assertTrue(created)
            self.assertEqual(path.name, "issue-57.md")
            self.assertIn("source_issue: 57", path.read_text(encoding="utf-8"))
            self.assertIn("college: 某学院", path.read_text(encoding="utf-8"))
            self.assertIn("major: 某专业", path.read_text(encoding="utf-8"))
            self.assertIn("## 我的经历", path.read_text(encoding="utf-8"))
            self.assertFalse(module.import_event(event, Path(directory), PEM)[1])

    def test_only_completed_signed_closure(self):
        for edit in (lambda x: x.update(action="reopened"),
                     lambda x: x["issue"].update(state_reason="not_planned"),
                     lambda x: x["repository"].update(full_name="other/repo"),
                     lambda x: x["issue"].update(title="not a submission"),
                     lambda x: x["issue"].update(labels=[]),
                     lambda x: x["issue"].update(body="invalid")):
            event = fixture()
            edit(event)
            with self.subTest(event=event), self.assertRaises(ValueError):
                with tempfile.TemporaryDirectory() as directory:
                    module.import_event(event, Path(directory), PEM)

    def test_unsafe_marker_and_yaml_are_rejected_or_quoted(self):
        event = fixture()
        event["issue"]["title"] = event["issue"]["title"].replace("某企业", "其它企业")
        with self.assertRaises(ValueError):
            module.decode_issue(event["issue"], PEM)
        event = fixture()
        event["issue"]["body"] += "\n" + event["issue"]["body"]
        with self.assertRaises(ValueError):
            module.decode_issue(event["issue"], PEM)

    def test_editing_signed_record_or_signature_is_rejected(self):
        event = fixture()
        event["issue"]["body"] = event["issue"]["body"].replace("v2:", "v2:A")
        with self.assertRaises(ValueError):
            module.decode_issue(event["issue"], PEM)
        event = fixture()
        event["issue"]["body"] = event["issue"]["body"].replace(" -->", "A -->")
        with self.assertRaises(ValueError):
            module.decode_issue(event["issue"], PEM)


if __name__ == "__main__":
    unittest.main()
