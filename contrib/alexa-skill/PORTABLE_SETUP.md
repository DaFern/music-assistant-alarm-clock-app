# Portable search and offset recovery candidate

This candidate builds on `alams154/music-assistant-alexa-skill-prototype` commit
`2967b60551250bcce50586e9de0f6b036dcff237`. It contains the search and callback
recovery changes exercised on one physical Echo, plus new per-player transport
isolation and offline regressions. The latter changes still need physical
multi-Echo acceptance. This is not a claim of support for every Echo model.

## What changes

- Music searches target the player paired with the requesting Echo. Exact-name
  ambiguity is reported rather than silently choosing between distinct URIs.
- MA flow and announcement publications are indexed by player. Mapped requests
  never use a different player's latest stream; unmapped requests cannot launch
  the global stream. Request-local metadata and APL capability prevent concurrent
  requests from sharing artwork or display settings.
- A failed flow can recover at the reported listening position through the
  matching MA server API. A stopped callback alone never triggers recovery.
  Pause, stop, next, search and fresh playback cancel an older recovery attempt.
- Pairing survives restarts when `instance_data` is mounted. The pairing page
  confirms a successful save and reports persistence failures.

No home addresses, room IDs, account tokens or personal device mappings are
included. Names containing spaces, apostrophes or Unicode are covered offline.

## Requirements and compatibility

Search uses `music-assistant-client==1.5.1`; the physically exercised MA server
was 2.10.12 (schema 65). A public HTTPS skill endpoint and public reachable audio
endpoint remain necessary. The same existing Alexa skill setup is used; this is
not a registered/default Alexa music provider.

Offset recovery additionally requires the authenticated
`player_queues/recover_alexa_flow` API from the companion server patch, currently
packaged in [MA Alarm Clock app 2.10.12-alarmclock.5](https://github.com/DaFern/music-assistant-alarm-clock-app/tree/6e0f51dd0ab4fbe22e7609a55870a68efc79a9a3).
That build-time patch checks the exact pinned MA source hash. It is not a patch
for arbitrary MA versions. Standard servers can use search and controls with
`ENABLE_ALEXA_OFFSET_RECOVERY=false` (the default). Only enable recovery after
installing a server with that API; there is no fallback that replays an expired URL.

The server retains permission checks, rejects stale streams, inactive queues,
grouped/synced players, ambiguous timelines and unseekable content. It uses MA's
flow mapper, not its advancing playback clock, and rewinds two seconds. Attempts
are bounded to two per queue within 120 seconds, once per failed session. These
bounds prevent loops; they do not cure the cause of a broken stream.

## Setup on any Docker host

1. Preserve your current image, source and data before replacing an installation.
   This candidate does not migrate or overwrite an existing deployment for you.
2. Copy `docker-compose.portable.yml` and configure `SKILL_HOSTNAME`, `SKILL_ID`,
   `MA_HOSTNAME` and `MA_API_URL` for your own installation. Hostnames are bare
   names (no scheme); the MA API value is a full base URL. Set `LOCALE` to match
   the Echo, e.g. `en-GB`.
3. Create private files `secrets/app_username.txt`, `secrets/app_password.txt`
   and `secrets/ma_api_token.txt`. Use a Music Assistant token with access to the
   intended players. Keep these files private and out of git. The example mounts
   them as secrets and persists both ASK credentials and device mappings.
4. Build/start with `docker compose -f docker-compose.portable.yml up -d --build`
   only when ready to change your installation. Configure the reverse proxies
   and existing skill setup as described in the main README. Keep authenticated
   management routes protected; Alexa's signed invocation endpoint must still
   be reachable by Amazon.
5. From **each Echo**, invoke your skill's help, refresh `/devices`, then pair the
   newly seen opaque Alexa device ID with that Echo's exact MA `player_id`.
   Display names are not guaranteed to equal IDs. The save confirms persistence,
   not that the ID exists or that playback works. No automatic room-name matching
   is attempted. Pair direct Echo players, not a tablet or unrelated group.
6. Upload/build the corresponding locale's interaction model using your existing
   skill setup or Alexa Developer Console. Search samples are included for all
   five English locale models. Keep the invocation name consistent with your
   skill and MA Alexa provider configuration. Other locales retain their prior
   models and need translated search samples before voice search is supported.
7. Say, for example, “Alexa, ask [your invocation name] to play songs by [artist]”.
   Use your Echo's configured wake word. “Find the album [title] by [artist]”
   and “find the song [title] by [artist]” provide media type hints.
   Preserve the slotless `PlayAudio` intent: MA uses “play audio” internally.
   Do not add a broad `play {query}` sample that captures that transport command.
8. Leave `ENABLE_ALEXA_OFFSET_RECOVERY=false` on a standard MA server. Set it to
   `true` and recreate the skill container only with the matching server API.

## Acceptance before calling this a release

Run offline tests with no live credentials:

```sh
python -m venv .venv
.venv/bin/pip install -r app/requirements.txt
.venv/bin/python -m unittest discover -s tests/portable -v
```

Then check fresh playback, pause/resume, a deliberate artist change, and independent
playback on at least two mapped Echos. Verify that a request on an unmapped device
cannot launch another room's stream. Verify that actual failure/stopped callbacks
recover the right item/position and that intentional pauses stay paused.

Streams and callback correlation are in-memory. After a skill restart, start fresh
playback from MA; old streams are not recovered from guessed positions. Multiple
web workers/processes are not supported by this in-memory transport design; use
one process (the supplied Flask deployment). Mapping names with literal slashes,
announcements with nonstandard route formats, grouped/synced players, missing
callbacks and live radio timelines have not been validated. APL display and
physical multi-Echo behavior need acceptance. No runtime deployment is performed
by applying the source patch or running the offline tests.
