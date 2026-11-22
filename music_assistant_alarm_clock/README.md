# Music Assistant — 2.10.12-alarmclock.8

The app and sidebar now use the Music Assistant name and icon. Alarm setup,
editing and playback messages refer to Music Assistant instead of a development
server. The existing app slug, data, queue handling and Alexa recovery patches
are unchanged.

# Repeat/Autoplay compatibility — 2.10.12-alarmclock.7

Scheduled alarm playback temporarily suspends enabled Repeat/Autoplay settings,
then conditionally restores the saved values on Snooze/Stop or guarded cleanup.
Matching HA integration source: `DaFern/HA-Alarm-Clock@8606f2d`.
The installed server advertises `queue_mode_lease`. The legacy experimental test
still requires those modes off. Grouping and ambient overlays remain unsupported.

This build retains the exact base image, Alexa recovery API and timeline patches
from .6. The new controller templates are pinned by commit and SHA256, downloaded
only during image build, and applied only after verifying the complete .6
controller hash. No data migration or provider-setting change is included.

Before updating, back up the existing app. Updating restarts Music Assistant and
interrupts playback; choose a time without an active alarm. After updating,
the matching HA integration still needs deployment and a separately approved Core
restart. Verify actual bedroom playback and mode restoration; CI is not physical
acceptance. Retain the .6 backup/build for rollback.

# Alexa timeline recovery — 2.10.12-alarmclock.6

Promoted from tested candidate commit `52da456d2182b047ea109db4c5f5d53dbc4fb6ef`.
Native amd64 image build, installed API/helper import, stream-hook verification and
26 focused runtime tests passed in CI run 44828182905. Physical acceptance of this
version remains pending; promotion does not install or restart a live app.

The pinned stream producer replaces `flow_mode_stream_log` whenever the same
session's URL is opened again. A late Alexa failure can therefore carry an
elapsed offset from the original connection, while the recovery API sees a short
new log. This candidate snapshots timing metadata immediately before that log is
replaced, for Alexa players only. It preserves seek positions, speeds, durations
and actual per-item streamed seconds; no audio or provider URLs are retained.

Snapshots expire after 120 seconds from replacement, with at most eight per queue,
32 queues and 256 entries per snapshot. Overflow refuses recovery. Only histories
from the current queue/session participate. Multiple valid timelines must agree
on item and position; otherwise recovery refuses with `ambiguous_stream_timeline`.
Incomplete boundaries still fail closed. The existing permission, session,
player, output/group, pause, takeover and retry-limit checks remain in force.

Both the controller and stream producer must match their pinned source hashes
before build-time changes are written. A small helper is installed beside the
controller. There are no data migrations, audio buffer changes, provider limit
changes or transport polling loops. The skill protocol is unchanged.

26 local offline recovery tests pass, including a reproduction using the reported
Dining Room offset (194517 ms), immutable seek/duration metadata, ambiguous history,
TTL expiry, new sessions, bounds and pause safety. Helper/controller compilation and diff checks pass. The full pinned flow module uses Python 3.14 syntax and cannot compile under the local Python 3.12 interpreter; its compilation is checked during the image build.
The repo's `pre-commit` executable is unavailable locally. Native image build/import
and runtime unit tests are defined in the existing candidate CI workflow. These
checks do not prove a fix for Office's missing failure callback or the cause of
simultaneous reconnects. Physical acceptance remains pending.

---

# 2.10.12-alarmclock.5 — Preserve stream identity across codec conversion

The Alexa skill rewrites MA flow URLs to MP3. Match the flow mode, session, queue, initial item and output-player filename while allowing known output-codec suffixes to differ. Retain all stale-session, permission, current-source, queue-state and retry guards. Focused tests cover format conversion and mismatched session/item/queue/output-player identities. No NAS module change or data migration is needed. Physical recovery acceptance remains pending.

# 2.10.12-alarmclock.4 — Alexa player-state compatibility

Fix the controlled-test AttributeError by checking group/sync membership on `player.state`, matching the pinned server's PlayerState model. Regression fixtures deliberately omit direct `active_group` and `synced_to` attributes and cover both grouped and synced rejection. No database, configuration or NAS module change is required. Physical recovery acceptance is still pending.

# Alexa offset recovery candidate — 2.10.12-alarmclock.3

This update preserves the existing app slug, base image and data schema. It adds the authenticated `player_queues/recover_alexa_flow` command, requiring queue-control scope and the existing player-permission check. It is used only by the matching NAS Alexa skill offset-recovery module.

Recovery requires a correlated Alexa playback failure and stopped event for the same stream token. The server uses its flow timeline and Alexa's stopped offset, never its advancing wall clock, and requests a fresh stream at the mapped queue item with a two-second rewind. It preserves queue items, rejects stale sessions, changed sources, grouped/paused/finished queues, ambiguous timing and missing media, and allows at most two attempts per queue per 120 seconds. An uncertain dispatch is consumed, not retried.

The Docker build verifies the exact original controller SHA256 before inserting the API and compiles the result. No startup downloads, dependency changes, database migrations, provider-setting changes or automatic playback tests are included. The CI build/import checks and offline tests do not prove audible recovery; a controlled physical test remains required. This is recovery after supported failures, not proof that the underlying handoff fault is fixed. Failures with no Alexa event are not recovered. Protection against every cross-device race in the existing shared-stream transport is outside this patch.

Before updating, back up this existing app through Supervisor. Do not migrate to a new slug or copy databases. Keep the .2 app build/backup for rollback. Deploy the server first and verify the new command is registered, then install the matching NAS skill module. Leaving the NAS module absent makes the new command passive. Keep fixed 48 kHz enabled during acceptance.

---

# MA – HA Alarm Clock

Dedicated app slug: `music_assistant_alarm_clock`. Version:
`2.10.12-alarmclock.2`. Experimental until live Supervisor/physical acceptance.

The Dockerfile pins the multi-architecture GHCR index:

```text
ghcr.io/dafern/music-assistant-alarm-clock-server@sha256:8a6fa5278b043c6f3f3afbe12728a7261657f900ec8c669d05318017f8a02bba
```

Companion source: `f0c825c708fcca577430aac46aa30f8cbf23b79b`, containing
the `aabb3e2` alarm lifecycle plus upstream Plex Connect backport `8258287`.
Matching HA integration source: 0.7.0b6 at `1bfd8db`; this does not deploy it.

[CI run 44572767798](https://github.com/DaFern/music-assistant-alarm-clock-app/actions/runs/44572767798)
passed on independent native amd64 and arm64 runners: fresh-data HTTP readiness,
Plex Connect import and hashes of all 12 overlaid source files. Registry manifest
bytes matched the index digest and anonymous pulls were available. CI did not
test Supervisor ingress, live providers, discovery or physical speakers.

The promoted manifest passed the app-linter JSON schema at
`frenck/action-addon-linter@d51677290aef26cdfc835271dd3c7343ce502809`, plus
checks for unique slug, option/schema alignment and types, architectures,
manual boot and exact Dockerfile digest. The registry index hash/platforms were
rechecked anonymously during promotion. Live Supervisor installation validation
is still pending; schema checks do not install the app.

## Installation and startup are separate approval gates

Add this repository only with live action-time approval:
`https://github.com/DaFern/music-assistant-alarm-clock-app`.
Select **MA – HA Alarm Clock**, not the unchanged upstream app definitions also
present in this fork. The repository-prefixed Supervisor slug must be discovered
from the store after adding it; do not guess it.

The app omits `image`: Supervisor builds a tiny local wrapper from the immutable
`FROM` index, inheriting the tested image's entrypoint and private `/data`.
Manual boot is the default. Leave watchdog and automatic updates disabled during
acceptance, and do not click Start or enable the sidebar until separately approved.
Installation/build without starting the container should not stop DEV; it still
uses host disk/network/CPU, so confirm at action time and monitor the build.

**Do not start alongside DEV unchanged.** The app uses host networking, ingress
port 8094 and the upstream MA server/stream/provider ports. Port mappings cannot
isolate a host-network app. A concurrent start is not a safe non-disruptive test.
A boot-only test needs an explicitly approved DEV maintenance window, or a
separately designed and validated isolated-network/different-host test.

## Rollback prerequisites and read-only preflight, 2026-11-19

- Supervisor 2026.11.0: healthy/supported, amd64; HAOS 18.3; 284.1 GB free.
  No active Supervisor jobs or Resolution issues were reported.
- DEV `d5369777_music_assistant_dev`: started, installed app version
  `2.11.0.dev2026111703`. Stable `d5369777_music_assistant`: already stopped,
  installed version `2.10.12`. Preserve those observed states.
- The dedicated fork was not registered in the live store; no custom app was
  installed. No store refresh, install, app start/stop, provider change or HA
  integration change was performed for this preflight.
- Backup `ffa20773` (2026-11-19 11:23 UTC) includes HA, its database and DEV.
  Full protected backup `8d8a878b` (00:00 UTC) includes both MA apps and HA,
  but reports HA history database excluded. Both report no failed components.
  Inventory is not a restore test; confirm access to the protected backup's
  encryption key and retrieve an off-host copy before a maintenance window.
- These backups predate later activity. Before any stop/start or migration,
  obtain approval for fresh matching DEV/stable/HA backups; prefer the supported
  app backup flow and avoid copying a running database. Do not restore the older
  HA+DEV backup over current settings just to test installation.
- Preserve current DEV/stable app images, private data, source pins and frontend/
  provider repository choices. The safe app inspection API withholds repository
  strings; their exact live values were **not independently verified**. Capture
  them securely through the app UI at action time, without publishing credentials.
  Historical DEV source `46b4183` is not a fresh runtime-pin verification.
- Preserve the current HA MA integration connection, alarm settings and deployed
  integration files; HA 0.7.0b6 remains a source candidate, not deployed here.
- Existing DEV logs include Plex PlayQueue 404s, Plex timeouts and Alexa
  throttling. This app's CI boot result does not prove those live issues fixed.

For a later boot-only test: confirm no alarm/playback is active, record DEV's
running state, install without starting, then request separate stop-DEV/start-
custom consent immediately before action. Use only the custom app's fresh private
data; do not copy DEV/stable databases or provider credentials, share `/data`,
reselect HA's integration, or play audio. After checking the build identity,
Supervisor logs and ingress, stop only the custom app and restore DEV's recorded
running state; leave stable's pre-existing state and both data sets intact.

Stop before all live actions until explicitly confirmed. Provider migration,
Charlotte's audiobook setup, HA deployment and cutover remain separate work.
