"""Build-time, hash-guarded queue-mode lease update; preserve Alexa recovery."""
import ast
import hashlib
import importlib.util
from pathlib import Path

EXPECTED = "c65595d46307435b81d96f062cd97dc76ff6f93a84484882d8bb71e79fd1cc26"


def candidate(raw, alarms, tests):
    """Construct and compile the complete controller before any writes."""
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise RuntimeError("Queue controller hash changed; refusing stale patch")
    # Docker ADD independently checks the pinned template hashes.
    source = raw.decode()
    start = '    @api_command("player_queues/briefing_test_capabilities", required_scope=Scope.QUEUES_CONTROL)\n'
    end = '    @api_command("player_queues/transfer", required_scope=Scope.QUEUES_CONTROL)\n'
    if source.count(start) != 1 or source.count(end) != 1:
        raise RuntimeError("Queue command insertion anchors changed")
    before, commands = source.split(start)
    _, after = commands.split(end)
    updated = before + tests + "\n" + alarms + "\n" + end + after
    # Preserve existing recovery hooks and cancel-before-dispatch behaviour, but
    # retain the exact alarm's external Stop/Pause intent across ownership loss.
    replacements = (
        (
            "        self._check_player_permission(queue_id)\n"
            "        self.mass.streams.audio.briefings.cancel_queue(queue_id)\n"
            "        await self._handle_stop(queue_id)",
            "        self._check_player_permission(queue_id)\n"
            "        alarm_command = self._capture_alarm_external_command(queue_id)\n"
            "        self.mass.streams.audio.briefings.cancel_queue(queue_id)\n"
            "        alarm_command_succeeded = False\n"
            "        try:\n"
            "            await self._handle_stop(queue_id)\n"
            "            alarm_command_succeeded = True\n"
            "        finally:\n"
            "            self._confirm_alarm_external_command(alarm_command, alarm_command_succeeded)",
        ),
        (
            "        self._check_player_permission(queue_id)\n"
            "        self.mass.streams.audio.briefings.cancel_queue(queue_id)\n"
            "        # cancel any pending play_index calls for this queue to prevent conflicts",
            "        self._check_player_permission(queue_id)\n"
            "        alarm_command = self._capture_alarm_external_command(queue_id)\n"
            "        self.mass.streams.audio.briefings.cancel_queue(queue_id)\n"
            "        # cancel any pending play_index calls for this queue to prevent conflicts",
        ),
        (
            "        await self.mass.players._handle_cmd_pause(queue_id)\n",
            "        alarm_command_succeeded = False\n"
            "        try:\n"
            "            await self.mass.players._handle_cmd_pause(queue_id)\n"
            "            alarm_command_succeeded = True\n"
            "        finally:\n"
            "            self._confirm_alarm_external_command(alarm_command, alarm_command_succeeded)\n",
        ),
    )
    for old, new in replacements:
        if updated.count(old) != 1:
            raise RuntimeError("External alarm command hook changed; refusing stale patch")
        updated = updated.replace(old, new, 1)
    tree = ast.parse(updated)
    compile(tree, "queue_controller.py", "exec")
    if "async def recover_alexa_flow(" not in updated:
        raise RuntimeError("Alexa recovery API must be retained")
    return updated


def main():
    spec = importlib.util.find_spec("music_assistant")
    if spec is None or spec.origin is None:
        raise RuntimeError("Music Assistant package not found")
    path = Path(spec.origin).parent / "controllers/player_queues/controller.py"
    here = Path(__file__).parent
    alarms = (here / "alarm_commands.py.txt").read_text()
    tests = (here / "test_commands.py.txt").read_text()
    result = candidate(path.read_bytes(), alarms, tests)
    path.write_text(result)
    print("Installed queue-mode lease:", hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
