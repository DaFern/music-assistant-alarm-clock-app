# Reusable Alexa skill candidate

This source-only package makes the search and offset-recovery work reusable
without personal addresses, device IDs, room names or secrets. It is stored here
alongside the server-side companion API; it is not installed by the MA app image.
It is not an upstream release or a claim that all Echo models have been tested.

[Setup, compatibility and acceptance checklist](PORTABLE_SETUP.md)

`portable-search-recovery.patch` is a git-format patch against:

- Repository: https://github.com/alams154/music-assistant-alexa-skill-prototype
- Exact base: `2967b60551250bcce50586e9de0f6b036dcff237`
- Candidate source commit: `6542f8a` (local development commit; the patch is the portable artifact)

The upstream license and notices are retained. No credentials, ASK data, mappings,
backup files or personal hostnames are packaged. The patch includes the new
modules, request/player isolation, pairing feedback, English models, opt-in
recovery configuration, an example compose file and 26 offline tests.

## Prepare source

Use a fresh checkout, not the directory running your current skill:

```sh
git clone https://github.com/alams154/music-assistant-alexa-skill-prototype.git alexa-candidate
cd alexa-candidate
git checkout --detach 2967b60551250bcce50586e9de0f6b036dcff237
git apply --check /path/to/portable-search-recovery.patch
git apply /path/to/portable-search-recovery.patch
python -m venv .venv
.venv/bin/pip install -r app/requirements.txt
.venv/bin/python -m unittest discover -s tests/portable -v
```

Applying and testing this patch performs no deployment or playback. Follow
`PORTABLE_SETUP.md` in the patched checkout to configure your own deployment.
Keep recovery disabled unless the MA server exposes the matching recovery API.
The included server patch in app version `2.10.12-alarmclock.5` provides that API;
the skill patch alone cannot add it to an unmodified MA server.

## Validation and remaining work

Locally: 26 offline tests pass on Python 3.12 with music-assistant-client 1.5.1;
compilation and `git diff --check` pass. The patch was applied to a fresh pinned
checkout and the tests passed there too. CI repeats patch application, imports,
compilation and tests without live credentials or audio commands.

The previously deployed recovery/search implementation has one physical Echo
success report, including recovery following a real failure and intentional
pause behavior. The new transport isolation, per-request APL capability and
pairing feedback are offline-tested, not physically accepted. Multi-Echo and APL
acceptance remain necessary. Server flow mapping/regression tests remain in
`tests/alexa_offset` in the containing repository. The underlying dropout cause
is not resolved by these recovery changes.

This candidate branch does not change the live NAS skill, Alexa cloud model,
Home Assistant app configuration, main branch or published app version. It does
not make Music Assistant a selectable Alexa default music service. Translated
models beyond English and a dedicated skill fork/upstream PR are follow-up work.

## Follow-up: verified player picker

Apply `pairing-player-picker.patch` **after** the original portable patch, in the
same fresh checkout. This adds a player dropdown with names, exact IDs and
availability. Saves validate the ID against a fresh MA player list; an unreachable
server cannot silently replace an existing mapping. Unavailable-but-known players
may be paired for later use. Voice search now explains when a speaker is unavailable.
Directory requests are read-only and limited to five seconds.

```sh
git apply --check /path/to/pairing-player-picker.patch
git apply /path/to/pairing-player-picker.patch
.venv/bin/python -m unittest discover -s tests/portable -v
```

The combined source passes **37 offline tests** (the original 26 plus 11 picker,
directory and error-message regressions). Compilation and whitespace checks pass.
The follow-up is source-only and has not been installed on the NAS; keep the
current dropout trial running until a later maintenance window. Existing mapping
files are preserved and need no migration. Automatic device identification is not
added: users still trigger a request from each Echo to identify its row.

For testing inside a built image, mount tests at `/app/tests` (beside `/app/app`),
set `PYTHONPATH=/app/app`, and discover `/app/tests/portable`. Mounting at `/tests`
breaks the locale-file assertions; the test layout expects the application and
tests to share a parent directory.
