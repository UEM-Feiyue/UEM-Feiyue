"""Verify the signed review domain for an Issue event."""
import json
import os
from pathlib import Path
from import_completed_submission import decode_issue, TEAMS

event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
record = decode_issue(event["issue"])
team = TEAMS[record["category"]]
with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
    output.write(f"team={team}\n")
print(f"Signed review category: {record['category']}; team: {team}")
