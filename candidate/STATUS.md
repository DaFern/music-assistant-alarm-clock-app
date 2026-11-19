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

## Blocker

The app commit push was rejected because the existing OAuth credential lacks
`workflow` scope. No workflow was created remotely, no build dispatched, no image
published and no candidate digest verified. Registry publication permission and
package visibility remain untested. No credential changes or bypass were attempted.

`app/config.yaml.template` prepares slug `music_assistant_alarm_clock`, preserving
the upstream Supervisor API/network/volume contract. It has no `image` field:
the final app must locally build the digest-pinned Dockerfile wrapper. Templates
are deliberately not exposed as an installable app until a verified digest exists.
The official app definitions remain unchanged.

## Next publication step

Use an explicitly authorized credential that can push Actions workflows, then:

1. Push this app branch and dispatch `alarmclock-candidate.yml` at its exact commit.
2. Require both amd64 and arm64 boot checks to succeed, inspect manifest platforms,
   review boot logs and source-hash evidence, and record the exact index digest.
3. Check registry visibility without changing it. If private, anonymous Supervisor
   pulls are blocked until a separately approved access/visibility arrangement.
4. Replace the digest placeholder, place the reviewed templates in
   `music_assistant_alarm_clock/` as `config.yaml` and `Dockerfile`, and commit/push.
5. Reconcile the HA project's packaging/handoff docs with the published app, then
   update Issue #2 after successful related commits and pushes.

## Separately approved Supervisor boot test (not performed)

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
