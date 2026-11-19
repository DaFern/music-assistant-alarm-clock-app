"""Fail closed unless the digest-pinned base matches every original source file."""

import ast
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path

overlay = Path("/opt/alarmclock/overlay")
manifest = json.loads((overlay / "build.json").read_text())
root = Path(importlib.util.find_spec("music_assistant").origin).resolve().parent.parent
assert importlib.metadata.version("defusedxml") == "0.7.1"
for name, hashes in manifest["files"].items():
    target = root / name
    actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
    assert actual == hashes["before"], f"Base source mismatch: {name}"
    content = (overlay / name).read_bytes()
    assert hashlib.sha256(content).hexdigest() == hashes["after"]
    if name.endswith(".py"):
        ast.parse(content, filename=name)
for name in manifest["files"]:
    (root / name).write_bytes((overlay / name).read_bytes())
(root / "alarmclock-build.json").write_text(json.dumps(manifest, indent=2) + "\n")
