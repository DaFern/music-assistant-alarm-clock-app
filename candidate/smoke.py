"""Boot the published digest with isolated, disposable container data."""

import json
import subprocess
import sys
import time
import urllib.request

image, platform = sys.argv[1:]
name = "alarmclock-ci-smoke"


def run(*args, **kwargs):
    return subprocess.check_output(["docker", *args], text=True, **kwargs)


try:
    run("run", "-d", "--name", name, "--platform", platform,
        "-p", "127.0.0.1:18095:8095", image)
    for attempt in range(120):
        if run("inspect", "-f", "{{.State.Running}}", name).strip() != "true":
            raise RuntimeError("Container exited before readiness")
        try:
            with urllib.request.urlopen("http://127.0.0.1:18095", timeout=3) as response:
                if response.status == 200:
                    break
        except Exception:
            time.sleep(2)
    else:
        raise RuntimeError("No HTTP readiness within 240 seconds")
    script = """
import hashlib, importlib.util, json
from pathlib import Path
from music_assistant.providers.plex_connect import plextv
root = Path(importlib.util.find_spec('music_assistant').origin).resolve().parent.parent
m = json.loads((root/'alarmclock-build.json').read_text())
for name, hashes in m['files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest() == hashes['after'], name
assert 'restore_playback' in (root/'music_assistant/controllers/player_queues/controller.py').read_text()
print(json.dumps(m))
"""
    print(run("exec", name, "/app/venv/bin/python", "-c", script))
    print(json.dumps({"platform": platform, "image": image, "http_ready": True}))
finally:
    subprocess.run(["docker", "logs", name], check=False)
    subprocess.run(["docker", "rm", "-fv", name], check=False)
