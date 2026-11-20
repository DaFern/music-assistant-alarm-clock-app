"""Install the guarded Alexa recovery API during the image build."""
import hashlib
import importlib.util
from pathlib import Path

EXPECTED_SOURCE_SHA256 = 'ea5b7d4131682bd5182a92fbfe5f65c6139e1ddb822e875ed36087ec07a5fe09'
METHOD = '    @api_command("player_queues/recover_alexa_flow", required_scope=Scope.QUEUES_CONTROL)\n    @handle_play_action\n    async def recover_alexa_flow(\n        self, queue_id: str, stream_path: str, offset_ms: int\n    ) -> dict[str, Any]:\n        """Recover an Alexa flow from its reported stream position."""\n        from urllib.parse import unquote, urlsplit\n\n\n        self._check_player_permission(queue_id)\n        parts = unquote(urlsplit(stream_path).path).strip("/").split("/")\n        if (isinstance(offset_ms, bool) or not isinstance(offset_ms, int)\n                or offset_ms < 0 or offset_ms > 604800000\n                or len(parts) != 5 or parts[0] != "flow" or parts[2] != queue_id):\n            return {"ok": False, "reason": "invalid_stream_position"}\n        data = self._queue_data.get(queue_id)\n        player = self.mass.players.get_player(queue_id)\n        if data is None or player is None or player.provider.domain != "alexa":\n            return {"ok": False, "reason": "not_alexa"}\n        queue = data.queue\n        if (data.session_id != parts[1] or queue.state != PlaybackState.PLAYING\n                or queue.ended or not queue.active or not queue.available\n                or player.state.active_group or player.state.synced_to\n                or not queue.flow_mode):\n            return {"ok": False, "reason": "stale_or_inactive"}\n        # Check the currently published stream as well as the session. Announcements\n        # and external playback must never restart the old music queue.\n        def stream_identity(value: str) -> tuple[str, ...] | None:\n            path = urlsplit(value).path.strip("/").split("/")\n            if len(path) != 5 or path[0] != "flow":\n                return None\n            path = [unquote(part) for part in path]\n            stem, separator, codec = path[-1].rpartition(".")\n            if not separator or codec.lower() not in {"mp3", "flac", "aac", "wav", "ogg", "pcm"}:\n                return None\n            return (*path[:-1], stem)\n\n        latest = getattr(player, "_last_stream_url", None)\n        identity = stream_identity(stream_path)\n        if not latest or identity is None or stream_identity(latest) != identity:\n            return {"ok": False, "reason": "newer_stream"}\n        from music_assistant.controllers.player_queues.alexa_recovery_timeline import resolve_position\n        resolved = resolve_position(self, queue_id, parts[1], offset_ms, PlaybackState.PLAYING)\n        if not resolved["ok"]:\n            return resolved\n        item = self.get_item(queue_id, resolved["item_id"])\n        position = resolved["position"]\n        if item is None:\n            return {"ok": False, "reason": "stale_or_inactive"}\n        now = time.monotonic()\n        history = getattr(self, "_alexa_recovery_history", {})\n        previous = history.get(queue_id, [])\n        previous = [(stamp, session) for stamp, session in previous if now - stamp < 120]\n        if any(session == parts[1] for _, session in previous) or len(previous) >= 2:\n            return {"ok": False, "reason": "retry_limit"}\n        if queue_id not in history and len(history) >= 256:\n            return {"ok": False, "reason": "recovery_state_full"}\n        history[queue_id] = previous + [(now, parts[1])]\n        self._alexa_recovery_history = history\n        seek = max(0, int(position) - 2)\n        # Consume before dispatch: an uncertain result must not replay the item twice.\n        await self._play_index(queue_id, item.queue_item_id, seek, False)\n        return {"ok": True, "item_id": item.queue_item_id, "position": seek}\n\n'
ANCHOR = '    @api_command("player_queues/play_index", required_scope=Scope.QUEUES_CONTROL)'

FLOW_SOURCE_SHA256 = '43f29852101908d4bd931565ce6b8b07bded61d3b80ce3b9d3b8d1ef90a2c731'
FLOW_ANCHOR = "        flow_log: list[PlayLogEntry] = []\n        pq_data.flow_mode_stream_log = flow_log"
FLOW_REPLACEMENT = "        from music_assistant.controllers.player_queues.alexa_recovery_timeline import remember_flow\n        remember_flow(self.mass.player_queues, queue.queue_id, flow_session_id)\n" + FLOW_ANCHOR


def main():
    spec = importlib.util.find_spec("music_assistant")
    if spec is None or spec.origin is None:
        raise RuntimeError("Music Assistant package not found")
    path = Path(spec.origin).parent / "controllers/player_queues/controller.py"
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Source hash mismatch; refusing to patch a different build")
    source = raw.decode()
    if source.count(ANCHOR) != 1:
        raise RuntimeError("Playback API insertion point changed")
    candidate = source.replace(ANCHOR, METHOD + ANCHOR, 1)
    compile(candidate, str(path), "exec")
    flow_path = path.parents[1] / "streams/audio.py"
    flow_raw = flow_path.read_bytes()
    if hashlib.sha256(flow_raw).hexdigest() != FLOW_SOURCE_SHA256:
        raise RuntimeError("Flow source hash mismatch; refusing to patch a different build")
    flow_source = flow_raw.decode()
    if flow_source.count(FLOW_ANCHOR) != 1:
        raise RuntimeError("Flow timeline insertion point changed")
    flow_candidate = flow_source.replace(FLOW_ANCHOR, FLOW_REPLACEMENT, 1)
    helper = Path(__file__).with_name("alexa_recovery_timeline.py").read_text()
    compile(flow_candidate, str(flow_path), "exec")
    compile(helper, "alexa_recovery_timeline.py", "exec")
    path.with_name("alexa_recovery_timeline.py").write_text(helper)
    flow_path.write_text(flow_candidate)
    path.write_text(candidate)
    print("Installed Alexa offset recovery API:", hashlib.sha256(path.read_bytes()).hexdigest())

if __name__ == "__main__":
    main()

