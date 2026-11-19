"""Export hash-guarded runtime changes from the exact companion checkout."""

import hashlib
import json
from pathlib import Path
import subprocess

BASE = "6ab5bfa63f02d0daa237d342097a42feae5c5aae"
REVISION = "f0c825c708fcca577430aac46aa30f8cbf23b79b"
source = Path("companion")
output = Path("candidate/overlay")


def git(*args):
    return subprocess.check_output(["git", "-C", str(source), *args])


assert git("rev-parse", "HEAD").decode().strip() == REVISION
records = {}
for name in git("diff", "--name-only", BASE, REVISION, "--", "music_assistant").decode().splitlines():
    current = git("show", f"{REVISION}:{name}")
    previous = subprocess.run(
        ["git", "-C", str(source), "show", f"{BASE}:{name}"], capture_output=True
    )
    if previous.returncode:
        assert not git("ls-tree", BASE, "--", name)
    target = output / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(current)
    records[name] = {
        "before": hashlib.sha256(previous.stdout).hexdigest() if previous.returncode == 0 else None,
        "after": hashlib.sha256(current).hexdigest(),
    }
assert records
(output / "build.json").write_text(json.dumps({
    "base_revision": BASE, "revision": REVISION, "files": records
}, indent=2) + "\n")
