"""Bounded, metadata-only flow timelines for conservative Alexa recovery."""
from dataclasses import dataclass
import math
import time
from types import SimpleNamespace

TTL = 120
MAX_QUEUES = 32
MAX_SNAPSHOTS = 8
MAX_ENTRIES = 256


@dataclass(frozen=True)
class Snapshot:
    """An isolated copy of the timing metadata before a producer is replaced."""

    stamp: float
    session: str
    queue_id: str
    entries: tuple
    items: dict


def remember_flow(controller, queue_id, session):
    """Remember the old producer before its timeline is replaced, for Alexa only."""
    player = controller.mass.players.get_player(queue_id)
    if player is None or player.provider.domain != "alexa":
        return
    now = time.monotonic()
    histories = getattr(controller, "_alexa_flow_snapshots", {})
    # Stale queues do not occupy the global bound indefinitely.
    histories = {key: value for key, value in histories.items()
                 if controller._queue_data.get(key) is not None
                 and value[2] > now - TTL
                 and value[0] == controller._queue_data[key].session_id}
    controller._alexa_flow_snapshots = histories
    if queue_id not in histories and len(histories) >= MAX_QUEUES:
        return
    previous = histories.get(queue_id, (session, [], now, False))
    snapshots = [value for value in previous[1]
                 if value.session == session and now - value.stamp <= TTL]
    overflow = previous[3] if previous[0] == session else False
    snapshot = _snapshot(controller, queue_id, session, now)
    data = controller._queue_data.get(queue_id)
    if snapshot is None and data is not None and data.flow_mode_stream_log:
        overflow = True
    if snapshot is not None:
        if len(snapshots) >= MAX_SNAPSHOTS:
            overflow = True
        else:
            snapshots.append(snapshot)
    histories[queue_id] = (session, snapshots, now, overflow)


def resolve_position(controller, queue_id, session, offset_ms, playback_state):
    """Resolve only positions on which all complete candidate timelines agree."""
    now = time.monotonic()
    histories = getattr(controller, "_alexa_flow_snapshots", {})
    if queue_id not in histories and len(histories) >= MAX_QUEUES:
        return {"ok": False, "reason": "timeline_history_overflow"}
    history = histories.get(queue_id)
    snapshots = []
    if history and history[0] == session and now - history[2] <= TTL:
        if history[3]:
            return {"ok": False, "reason": "timeline_history_overflow"}
        snapshots.extend(value for value in history[1] if now - value.stamp <= TTL)
    current = _snapshot(controller, queue_id, session, now)
    if current is not None:
        snapshots.append(current)
    elif controller._queue_data[queue_id].flow_mode_stream_log:
        return {"ok": False, "reason": "timeline_not_finalized"}
    results = []
    reasons = []
    for snapshot in snapshots:
        result = _resolve_snapshot(controller, snapshot, offset_ms, playback_state)
        if result["ok"]:
            results.append(result)
        else:
            reasons.append(result["reason"])
    if not results:
        reason = "timeline_not_finalized" if "timeline_not_finalized" in reasons else "offset_outside_timeline"
        return {"ok": False, "reason": reason}
    # An incomplete candidate might place this same offset on a different item.
    if "timeline_not_finalized" in reasons:
        return {"ok": False, "reason": "timeline_not_finalized"}
    first = results[0]
    if any(value["item_id"] != first["item_id"]
           or abs(value["position"] - first["position"]) > 0.01 for value in results[1:]):
        return {"ok": False, "reason": "ambiguous_stream_timeline"}
    return first


def _snapshot(controller, queue_id, session, now):
    data = controller._queue_data.get(queue_id)
    if data is None or data.session_id != session or not data.flow_mode_stream_log:
        return None
    if len(data.flow_mode_stream_log) > MAX_ENTRIES:
        return None
    entries = []
    items = {}
    for entry in data.flow_mode_stream_log:
        # Repeated items can have different seek bases; the shared QueueItem cannot prove them.
        if entry.queue_item_id in items:
            return None
        item = controller.get_item(queue_id, entry.queue_item_id)
        if item is None:
            return None
        details = item.streamdetails
        items[entry.queue_item_id] = SimpleNamespace(
            queue_item_id=item.queue_item_id, duration=item.duration,
            extra_attributes={"playback_speed": item.extra_attributes.get("playback_speed")},
            streamdetails=SimpleNamespace(seconds_streamed=details.seconds_streamed,
                seek_position=details.seek_position) if details else None)
        entries.append(SimpleNamespace(queue_item_id=entry.queue_item_id,
                                       seconds_streamed=entry.seconds_streamed))
    return Snapshot(now, session, queue_id, tuple(entries), items)


def _resolve_snapshot(controller, snapshot, offset_ms, playback_state):
    total = 0.0
    for index, entry in enumerate(snapshot.entries):
        item = snapshot.items[entry.queue_item_id]
        seconds = entry.seconds_streamed
        if seconds is None:
            seconds = item.streamdetails.seconds_streamed if item.streamdetails else None
        if seconds is None and index == len(snapshot.entries) - 1:
            if not item.duration or not item.streamdetails:
                return {"ok": False, "reason": "timeline_not_finalized"}
            speed = float(item.extra_attributes.get("playback_speed") or 1.0)
            if not math.isfinite(speed) or speed <= 0:
                return {"ok": False, "reason": "timeline_not_finalized"}
            seconds = max(0, item.duration - item.streamdetails.seek_position) / speed
        if seconds is None or not math.isfinite(seconds) or seconds < 0:
            return {"ok": False, "reason": "timeline_not_finalized"}
        total += seconds
    if offset_ms / 1000 > total + 0.25:
        return {"ok": False, "reason": "offset_outside_timeline"}
    ids = list(snapshot.items)
    def get_item(_, index):
        return snapshot.items.get(ids[index]) if isinstance(index, int) and 0 <= index < len(ids) else None
    proxy = SimpleNamespace(
        _queue_data={snapshot.queue_id: SimpleNamespace(flow_mode_stream_log=snapshot.entries)},
        index_by_id=lambda _, item_id: ids.index(item_id) if item_id in ids else None,
        get_item=get_item)
    queue = SimpleNamespace(queue_id=snapshot.queue_id, current_index=0, elapsed_time=0)
    frozen = SimpleNamespace(state=SimpleNamespace(corrected_elapsed_time=offset_ms / 1000,
                                                  playback_state=playback_state))
    index, position = type(controller)._get_flow_queue_stream_index(proxy, queue, frozen)
    item = get_item(snapshot.queue_id, index)
    if (item is None or not item.duration or not math.isfinite(position)
            or position < 0 or position >= item.duration):
        return {"ok": False, "reason": "unseekable_position"}
    return {"ok": True, "item_id": item.queue_item_id, "position": position}
