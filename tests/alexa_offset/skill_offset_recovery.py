"""Forward correlated Alexa failures and stopped offsets to the MA recovery API."""
import asyncio
import logging
import threading
import time
from urllib.parse import unquote, urlsplit

logger = logging.getLogger(__name__)
_lock = threading.Lock()
_devices = {}


def canonical(token):
    if not isinstance(token, str):
        return None
    parts = urlsplit(token).path.strip('/').split('/')
    if len(parts) != 5 or parts[0] != 'flow':
        return None
    return tuple(unquote(part) for part in parts)


def started(device, token):
    with _lock:
        state = _devices.setdefault(device, {'generation': 0})
        state.update(token=canonical(token), generation=state['generation'] + 1,
                     cancelled=False, failure=None, stopped=None)


def cancel(device):
    with _lock:
        state = _devices.get(device)
        if state:
            state.update(cancelled=True, generation=state['generation'] + 1)


def claim(state):
    failure, stopped = state.get('failure'), state.get('stopped')
    if (state.get('cancelled', True) or not failure or not stopped
            or abs(failure[0] - stopped[0]) > 10 or state.get('busy')
            or state.get('attempted') == (state['generation'], state['token'])):
        return None
    state['attempted'] = (state['generation'], state['token'])
    state['busy'] = True
    return state['generation'], stopped[1], stopped[2]


def event(device, token, offset=None, failure=False):
    key = canonical(token)
    if key is None:
        return
    with _lock:
        state = _devices.get(device)
        if not state or state.get('token') != key or state.get('cancelled'):
            return
        if failure:
            state['failure'] = (time.monotonic(),)
        elif isinstance(offset, int) and not isinstance(offset, bool) and 0 <= offset <= 604800000:
            state['stopped'] = (time.monotonic(), offset, token)
        action = claim(state)
    if action:
        generation, milliseconds, original_token = action
        threading.Thread(target=worker, args=(device, key, generation, milliseconds,
                         original_token), daemon=True, name='alexa-offset-recovery').start()


def current(device, key, generation):
    with _lock:
        state = _devices.get(device, {})
        return (not state.get('cancelled', True) and state.get('token') == key
                and state.get('generation') == generation)


async def dispatch(device, key, generation, offset, token):
    import aiohttp
    from env_secrets import get_env_secret
    from music_assistant_client import MusicAssistantClient
    from .device_mapping import get_player_for_device

    player = get_player_for_device(device)
    if not player or key[2] != player:
        logger.warning('Recovery skipped: device mapping does not match failed stream')
        return
    async with aiohttp.ClientSession() as session:
        async with MusicAssistantClient(get_env_secret('MA_API_URL'), session,
                                        token=get_env_secret('MA_API_TOKEN')) as client:
            for _ in range(4):
                if not current(device, key, generation):
                    return
                result = await client.send_command('player_queues/recover_alexa_flow',
                    queue_id=player, stream_path=urlsplit(token).path, offset_ms=offset)
                logger.warning('Alexa offset recovery result: %s', result)
                if result.get('reason') != 'timeline_not_finalized':
                    return
                await asyncio.sleep(0.5)


def worker(device, key, generation, offset, token):
    try:
        asyncio.run(asyncio.wait_for(dispatch(device, key, generation, offset, token), 12))
    except Exception:
        logger.exception('Alexa recovery failed; expired URL was not replayed')
    finally:
        with _lock:
            if device in _devices:
                _devices[device]['busy'] = False
