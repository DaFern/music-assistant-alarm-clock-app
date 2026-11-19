# MA – HA Alarm Clock candidate

Dispatch `Alarm Clock candidate` from an exact app commit. The workflow overlays
the exact companion revision onto a digest-pinned upstream 2.10.12 image; every
replaced original must match its upstream Git hash. No dependency resolution,
startup Git pull or runtime installer is added. The upstream venv, bundled
binaries and entrypoint are preserved. `defusedxml==0.7.1` is checked at build time.

Version: `2.10.12-alarmclock.2`. Companion:
`f0c825c708fcca577430aac46aa30f8cbf23b79b`, containing `aabb3e2` plus
Plex Connect backport `8258287` and its explicit safe XML dependency declaration.
The corresponding HA integration remains source-only 0.7.0b6 (`1bfd8db`).

CI publishes amd64/arm64, records the index digest and boots each platform on a
private Docker bridge with fresh disposable data and no HA/provider credentials.
HTTP readiness, Plex imports and all overlaid source hashes are checked. This is
not Supervisor or physical-speaker acceptance. Evidence is retained as an Actions
artifact; registry visibility is not changed. A private package cannot be pulled
anonymously by Supervisor without separate access arrangements.

The verified wrapper is now in `../music_assistant_alarm_clock/`, pinned to index
`sha256:8a6fa5278b043c6f3f3afbe12728a7261657f900ec8c669d05318017f8a02bba`.
Run 44572767798 passed both native architecture boot jobs without rebuilding.
Do not install, start the app, stop DEV, copy runtime data, or cut over HA without
separate live action-time approval. See the app README for preflight/rollback.
