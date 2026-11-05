"""Import only a reviewed, completed UEM GitHub Issue into canonical Markdown."""
import base64
import json
import os
from pathlib import Path
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "data/schema.json").read_text(encoding="utf-8"))
MARKER = re.compile(r"^<!-- uem-submission-v1:([A-Za-z0-9_-]+) -->$", re.M)
ISSUE_PREFIX = "[飞跃手册投稿] "


def validate_record(value):
    if not isinstance(value, dict) or value.get("version") != 1:
        raise ValueError("Unknown submission version")
    if value.get("category") not in {x["id"] for x in SCHEMA["categories"]}:
        raise ValueError("Invalid category")
    allowed = {"version", "category"} | {x["name"] for x in SCHEMA["fields"]}
    if set(value) != allowed:
        raise ValueError("Unexpected or missing fields")
    for field in SCHEMA["fields"]:
        item = value[field["name"]]
        if not isinstance(item, str) or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", item):
            raise ValueError("Invalid field type")
        if field.get("required") and not item.strip():
            raise ValueError("Missing field")
        if field.get("maxLength") and len(item.strip()) > field["maxLength"]:
            raise ValueError("Oversized field")
        if field.get("pattern") and item and not re.fullmatch(field["pattern"], item):
            raise ValueError("Invalid field pattern")
    return value


def decode_issue(issue):
    if not isinstance(issue, dict) or not str(issue.get("title", "")).startswith(ISSUE_PREFIX):
        raise ValueError("Not a submission Issue")
    if not any(label.get("name") == "submission:pending" for label in issue.get("labels", [])):
        raise ValueError("Pending submission label is required")
    body = issue.get("body") or ""
    marks = MARKER.findall(body)
    if len(marks) != 1 or len(marks[0]) > 86000:
        raise ValueError("Expected exactly one valid submission marker")
    encoded = marks[0]
    raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    if len(raw) > 65536:
        raise ValueError("Submission record oversized")
    record = validate_record(json.loads(raw.decode("utf-8")))
    title = record["author"] + " — " + record["destination"]
    if record["program"]:
        title += " · " + record["program"]
    category_label = next(x["label"] for x in SCHEMA["categories"] if x["id"] == record["category"])
    expected_title = ISSUE_PREFIX + "[" + category_label + "] " + re.sub(r"\s+", " ", title)[:95]
    if issue["title"] != expected_title:
        raise ValueError("Issue title and verified data differ")
    return record


def import_event(event, root=ROOT):
    if event.get("action") != "closed" or event.get("issue", {}).get("state_reason") != "completed":
        raise ValueError("Only completed closures are publishable")
    if event.get("sender", {}).get("login") != "FuTseYi":
        raise ValueError("Only the designated maintainer can approve")
    issue = event["issue"]
    if issue.get("pull_request") or not isinstance(issue.get("number"), int) or not (1 <= issue["number"] <= 9999999):
        raise ValueError("Invalid Issue")
    if event.get("repository", {}).get("full_name") != "UEM-Feiyue/UEM-Feiyue.github.io":
        raise ValueError("Wrong repository")
    record = decode_issue(issue)
    target = root / "content" / "community" / ("issue-" + str(issue["number"]) + ".md")
    if target.exists():
        return target, False
    frontmatter = {name: record[name] for name in ("category", "author", "year", "destination", "program", "contact") if record[name]}
    frontmatter["source_issue"] = issue["number"]
    target.parent.mkdir(parents=True, exist_ok=True)
    content = "---\n" + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False) + "---\n" + record["body"].strip() + "\n"
    target.write_text(content, encoding="utf-8")
    return target, True


def main():
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH is required")
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    target, created = import_event(event)
    print(("Imported " if created else "Already imported ") + str(target.relative_to(ROOT)))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Submission import rejected: {exc}", file=sys.stderr)
        sys.exit(1)
