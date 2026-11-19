# Publication status — 2026-11-19

## Verified source

- HA 0.7.0b6: `1bfd8db3c7eb17cf46de3b80e965da3061cbf33b` (unchanged).
- Companion starting revision: `aabb3e2af2e6c0a3e27b6af8dd1cc4b3c18c660d`.
- Plex upstream backport: `8258287cb4d09ecfd3f041f7e689af7395623c69`,
  clean cherry-pick `43e2343`.
- Final companion: `f0c825c708fcca577430aac46aa30f8cbf23b79b` (pushed).
  Declared `defusedxml==0.7.1` directly in the Plex Connect manifest;
  this exact version was already in requirements_all.txt.
- Plex suite: 99 passed. HA/native regression suite: 309 passed, no skips.
- Targeted mypy: 12 files passed. Full pre-commit attempted: method-order
  violations in the existing alarm controller and broad mypy failures with the
  partial provider dependency environment; all other hooks passed.
- Native tests require the original, hash-guarded upstream fixture. Pointing
  them at patched companion source correctly failed the fixture guard; the
  subsequent valid fixture run passed all 309 tests.

## Published and boot-verified

The initial workflow-scope blocker was resolved with user-approved GitHub browser
authorization. App source was pushed and run 44571220076 built/published version
`2.10.12-alarmclock.2`. Its sequential arm64 test hit a Docker image-store conflict;
amd64 passed. Commit `7e87a4a` separated native architecture tests. Verification-only
run 44572767798 passed amd64 and arm64 against the unchanged index:

`sha256:8a6fa5278b043c6f3f3afbe12728a7261657f900ec8c669d05318017f8a02bba`

Both artifacts verified HTTP readiness, Plex import and all 12 overlaid source
hashes. Independent anonymous registry access verified the index hash and both
platforms; visibility was not changed.

## Dedicated app promotion

`../music_assistant_alarm_clock/config.yaml` promotes the dedicated slug with
manual boot. Its Dockerfile pins the exact verified index. There is no `image`
field: Supervisor locally builds the digest-pinned wrapper. Official app
definitions remain unchanged. Promotion is source-only, not live installation.
The app README records read-only Supervisor preflight and rollback prerequisites.

## Separately approved Supervisor boot test (not performed)

DEV was started and stable was already stopped at preflight; preserve both states.
Back up DEV/stable and retain their exact pins/data and HA integration connection.
With explicit install/stop approval and no active alarm, add the app fork repository
through Supervisor's store UI, refresh it, and install the digest-pinned dedicated
app with start-on-boot and watchdog disabled initially. Do not copy or share DEV
or stable runtime directories: use the dedicated app's fresh private `/data`.

Because it uses host networking and the inherited MA ports (including 8094/8095),
stop DEV before starting the dedicated app; identify and stop any other conflicting
instance only with separate explicit consent. Do not change stable's configuration.
Start the dedicated app, verify Supervisor/ingress/API readiness and exact build
revision, then stop it and restore DEV's prior running state for a boot-only test.
Do not reconfigure the live HA integration or add providers during this test.

Provider migration, Charlotte's audiobook setup, physical speaker playback,
HA 0.7.0b6 deployment and cutover remain separate acceptance work under Issue #2.
CI boot success cannot establish Supervisor or physical playback acceptance.
