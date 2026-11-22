"""Verify exact tested command ASTs in the built app, retaining recovery hooks."""
import ast
import inspect
from pathlib import Path

from music_assistant.controllers.player_queues.controller import PlayerQueuesController
import music_assistant.controllers.streams.audio as audio


def methods(source):
    tree = ast.parse(source)
    host = next(node for node in tree.body if isinstance(node, ast.ClassDef))
    return {node.name: ast.dump(node, include_attributes=False)
            for node in host.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


root = Path("/workspace/alarm-project/prototypes/ma_one_shot")
expected = methods("class Host:\n" + (root / "test_commands.py.txt").read_text()
                   + "\n" + (root / "alarm_commands.py.txt").read_text())
installed = methods(inspect.getsource(PlayerQueuesController))
for name, body in expected.items():
    assert installed.get(name) == body, f"Installed method differs: {name}"
assert callable(PlayerQueuesController.recover_alexa_flow)
assert "remember_flow(" in inspect.getsource(audio)
manifest = Path("/workspace/music_assistant_alarm_clock/config.yaml").read_text()
assert 'name: "Music Assistant"' in manifest
assert 'panel_title: "Music Assistant"' in manifest
assert "panel_icon: mdi:music-assistant" in manifest
assert "slug: music_assistant_alarm_clock" in manifest
print("All tested alarm methods and Alexa recovery hooks verified")
