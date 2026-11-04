"""UEM business build: sanitized Markdown articles and archive data."""
import shutil
import subprocess
import sys

SOURCE_FILES = ("index.html", "submit.html")
SOURCE_DIRS = ("content", "data")


def build(root, destination, options):
    candidate = destination.parent / "source"
    candidate.mkdir()
    for name in ("assets", "content", "data", "scripts"):
        shutil.copytree(root / name, candidate / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in SOURCE_FILES:
        shutil.copy2(root / name, candidate / name)
    result = subprocess.run([sys.executable, str(candidate / "scripts/build.py")],
                            cwd=candidate, capture_output=True, encoding="utf-8", errors="replace")
    if result.returncode:
        sys.stderr.write(result.stdout + result.stderr)
        raise subprocess.CalledProcessError(result.returncode, "build.py")
    destination.mkdir()
    for name in SOURCE_FILES:
        shutil.copy2(candidate / name, destination / name)
    for name in ("assets", "articles"):
        shutil.move(str(candidate / name), str(destination / name))
    public_data = destination / "data"
    public_data.mkdir()
    for name in ("schema.json", "articles.json", "demo-submission.md"):
        shutil.copy2(candidate / "data" / name, public_data / name)
    return ([result.stdout.strip()], [])
